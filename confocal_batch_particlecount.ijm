//MP-VAT Batch Processing (Microplastics Visual Analysis Tool) v1.0

//Original Implimentation J.C.Prata, V. Reis, J. Matos, J.P.da Costa, A.Duarte, T.Rocha-Santos, 2019
//Expanded for batch processing by W. Cowger 2020
//Edited for Frantz Lab confocal files (3-channel Olympus *.oir files) by C. Frantz 2025
//	incorporating some suggestions from Chen et al 2021

//Macro does the following:
//1. Selects image files from an input folder
//2. Splits channels, runs process only on the specified channel
//3. Applies the user-specified scale
//4. Runs an 8-bit color conversion, user-specified threshold, and denoise
//5. Identifies Fibers, Fragments, and Particles
//6. Exports counts, Feret's diameter, and areas to csv files


// ====================
// USER INPUT GUI (This only works in ImageJ, not Fiji)
// ====================
//#@ File (label = "Input directory", style = "directory") input
//#@ File (label = "Output directory", style = "directory") output
//#@ String (label = "File suffix", value = ".oir") suffix
//#@ Float (label = "Pixel size (microns)", value = "0.994") pixscale
//#@ Integer (label = "Total number of channels", value = "3") nchan
//#@ Integer (label = "Channel to analyze", value = "1") vchan
//#@ Integer (label = "Transmitted light channel", value = "3") tlchan
//#@ Float (label = "Threshold min to use (must be > 0)", value = "12") thresh
//#@ Boolean (label = "Apply denoising?", value=false) doDenoise
//#@ Boolean (label = "Save QC images?") saveQC
//
//inputDir = input.getAbsolutePath() + File.separator;
//outputDir = output.getAbsolutePath() + File.separator;


// ====================
// DEFINE VARIABLES
// ====================

// --- Manual Definitions ---
suffix = ".oir";
pixscale = 0.994;
nchan = 3;
vchan = 1;
// thresh = 252;
doDenoise = true;
saveQC = true;

// --- User Input ---
inputDir = getDirectory("Choose input directory");
outputDir = getDirectory("Choose output directory");
//suffix = getString("File suffix", ".oir");
//pixscale = getNumber("Pixel size (microns)", 0.994);
//nchan = getNumber("Total channels", 3);
//vchan = getNumber("Channel to analyze", 1);

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
function microplasticAnalysis(mpType, circ_min, circ_max) {
	outPath =  outputDir + baseFileName + "_" + mpType + ".csv";

	run("Clear Results");
	
	selectWindow("working");
	
	// Watershed accounts for overlapping particles
	if (mpType == "particles") {
		run("Watershed");
		}
		
	// Analyze particles
	run("Analyze Particles...", "size=3-1000000 pixel circularity=" + circ_min + "-" + circ_max + " show=Overlay display summarize");
	
	// Check results
	if (nResults > 0) {
		selectWindow("Results");
		print(mpType + ": " + nResults);
		saveAs("Results", outPath);
		close();
	} else {
		print(mpType + ": 0");
		File.saveString("No particles detected", outPath);
		}
		
	while (isOpen("Results")) {
		selectWindow("Results");
		run("Close");
		}
	
	while (isOpen("Summary")) {
		selectWindow("Summary");
		run("Close");
		}
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
	
	// --- Open file to create saved composite ---
	run("Bio-Formats Importer", "open=[" + inputDir + file + "] color_mode=Composite view=Hyperstack stack_order=XYCZT");
	saveAs("Jpeg", outputDir + baseFileName + "_composite.jpg");
	close();
	
	// --- Open file for analysis --- 
	run("Bio-Formats Importer", "open=[" + inputDir + file + "] Autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");

	originalTitle = getTitle();
	
	// --- Split channels --- 
	run("Split Channels");

	titles = getList("image.titles");
	
	// --- Run process on the specified channel (Expected channel naming: C1-filename) --- 
	analysisCh = getChannelWindow(vchan);

	if (analysisCh == "") {
		close("*");
		continue;
	}
	
	
	// --- Save tiff images of each channel ---
	titles = getList("image.titles");

	for (c = 1; c <= nchan; c++) {
		chName = getChannelWindow(c);

		if (chName != "") {
			selectWindow(chName);
			run("Duplicate...", "title=view_copy");
			selectWindow("view_copy");
			//run("Enhance Contrast...", "saturated=0.35");
			saveAs("Jpeg", outputDir + baseFileName + "_C" + c + ".jpg");
			close();
		} else {
			print("WARNING: Channel " + c + " not found for saving.");
		}
	}
	
	
	selectWindow(analysisCh);
	rename("working");


    // --- Close all other windows ---
    titles = getList("image.titles");
    for (i = 0; i < titles.length; i++) {
        if (titles[i] != "working" && titles[i] != "original_copy") {
            selectWindow(titles[i]);
            close();
        }
    }
	  
    // --- Set the scale ---
    run("Set Scale...", "distance=1 known=" + pixscale + " pixel=1 unit=micron");
	  
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
	if (saveQC) {
		saveAs("Jpeg", outputDir + baseFileName + "_mask.jpg");
	}
	
	// --- Define and analyze three types of shapes:  ---
	
	// 		Fibers (low circularity)
	microplasticAnalysis("fibers", 0.0, 0.3);

	//		Fragments (med circularity)
	microplasticAnalysis("fragments", 0.3, 0.6);

	//		Particles
	microplasticAnalysis("fragments", 0.6, 1.0);
	
	
	print("Finished: " + file);

}

setBatchMode(false);