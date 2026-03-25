//Based off of MP-VAT Batch Processing (Microplastics Visual Analysis Tool) v1.0
//Original Implimentation J.C.Prata, V. Reis, J. Matos, J.P.da Costa, A.Duarte, T.Rocha-Santos, 2019
//Expanded for batch processing by W. Cowger 2020
//Edited for Frantz Lab confocal files (3-channel Olympus *.oir files) by C. Frantz 2025
//	incorporating some suggestions from Chen et al 2021

//Macro does the following:
//1. Selects image files from an input folder
//2. Splits channels, runs process only on the specified channel
//4. Runs an 8-bit color conversion, user-specified threshold, and denoise
//5. Identifies Fibers, Fragments, and Particles
//6. Exports counts, Feret's diameter, and areas for each particle type to a csv file

//Inputs:
//Directory containing *.oir image stack files from Olympus Confocal microscope
//	Assumes that scale is saved in the native file
//	Analysis is conducted on the channel specified in Define Variables
//Output directory

// ====================
// DEFINE VARIABLES
// ====================

// --- Manual Definitions ---
suffix = ".oir";
nchan = 3;
vchan = 1;
doDenoise = true;
saveMask = true;

// --- User Input ---
inputDir = getDirectory("Choose input directory");
outputDir = getDirectory("Choose output directory");

// Auto vs. manual thresholding
threshStr = getString("Threshold (type 'auto' for automatic thresholding, or enter an integer between 0-255)","auto");
if (indexOf(threshStr, "auto") != -1 ) {
	doAutoThresh = true;
	} else {
		doAutoThresh = false;
		thresh = parseInt(threshStr);
		
		if (thresh < 0 || thresh > 255) {
			exit("Threshold must either be 'auto' or an integer between 0 and 255");
		}
	}



// =======================
// WINDOW PARSING FUNCTION
// =======================
function getChannelWindow(chan) {

    titles = getList("image.titles");

    for (i = 0; i < titles.length; i++) {

        t = titles[i];

        // Match patterns like:
        // C1-..., C2-..., etc.
        if (startsWith(t, "C" + chan + "-")) {
            return t;
        }
    }
	
	// Fallback: if channel 1 was renamed to "working"
    if (chan == vchan && isOpen("working")) {
        return "working";
    }

    // If nothing found, print debug info
    print("ERROR: Channel " + chan + " not found.");
    print("Available windows:");
    for (i = 0; i < titles.length; i++) {
        print("  " + titles[i]);
    }

    return "";
}



// ====================
// SETUP
// ====================

// --- Parse the list of files ---
filelist = getFileList(inputDir);

setBatchMode(true);

// --- Define the measurements to run ---
run("Set Measurements...", "area shape feret's display redirect=None decimal=3");


// =======================
// PARTICLE ANALYSIS FUNCTION
// =======================
function microplasticAnalysis(image, mpType, circ_min, circ_max) {
	
	start = nResults;
	
	selectWindow(image);
	run("Duplicate...", "title=temp");
	selectWindow("temp");
	
	// Watershed accounts for overlapping particles
	if (mpType == "particles") {
		run("Watershed");
		}
		
	// Analyze particles
	run("Analyze Particles...", "size=3-1000000 pixel circularity=" + circ_min + "-" + circ_max + " show=Overlay display summarize");
	end = nResults;
	
	
	// Add particle type label to new results rows
	for (r = start; r < end; r++) {
		setResult("Type", r, mpType);
	}
	
	// Check results
	if (nResults > 0) {
		print(mpType + ": " + nResults);
	} else {
		print(mpType + ": 0");
		}
		
	// Close the temp image
	selectWindow("temp");
	close();
		
	}


// =======================
// MAIN LOOP
// =======================

for (f = 0; f < filelist.length; f++) {

	// --- Check that the file has the correct extension --- 
	file = filelist[f];
	if (!endsWith(file, suffix)) continue;
	
	print("Processing: " + file);
	baseFileName = replace(file, suffix, "");
	
	// --- Open file for analysis --- 
	run("Bio-Formats Importer", "open=[" + inputDir + file + "] Autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");

	originalTitle = getTitle();
	
	// --- Split channels --- 
	run("Split Channels");
	
	// --- Run process on the specified channel (Expected channel naming: C1-filename) --- 
	analysisCh = getChannelWindow(vchan);

	if (analysisCh == "") {
		print("Analysis channel " + vchan + "not found.")
		close("*");
		continue;
	}
	
	selectWindow(analysisCh);
	  
    // --- Preprocessing ---
	run("Invert");
	run("8-bit");
	
	// --- Threshold ---
	if (doAutoThresh) {
		setAutoThreshold("MaxEntropy");
	} else {
		setThreshold(0, thresh);
	}
	setOption("BlackBackground", false);
    run("Convert to Mask");
	
	// --- Optional denoise steps recommended by Chen et al., 2021 ---
	if (doDenoise) {
		run("Despeckle");
		run("Remove Outliers...", "radius=1 threshold=40 which=Bright");
		run("Remove Outliers...", "radius=1 threshold=40 which=Dark");
	}
	
	// --- Save mask QC image ---
	if (saveMask) {
		run("Duplicate...", "title=view_copy");
		selectWindow("view_copy");
		saveAs("Jpeg", outputDir + baseFileName + "_mask.jpg");
	}
	
	// --- Define and analyze three types of shapes:  ---
	run("Clear Results");
	
	// 		Fibers (low circularity)
	microplasticAnalysis(analysisCh, "fibers", 0.0, 0.3);

	//		Fragments (med circularity)
	microplasticAnalysis(analysisCh, "fragments", 0.3, 0.6);

	//		Particles
	microplasticAnalysis(analysisCh, "particles", 0.6, 1.0);
	
	// --- Save the results ---
	for (r = 0; r < nResults; r++) {
		setResult("Image", r, baseFileName);
	}
	outPath =  outputDir + baseFileName + ".csv";
	saveAs("Results", outPath);
	
	// --- Close all windows ---
    close("*");
	
	print("Finished: " + file);

}

setBatchMode(false);

print("Done with set.");