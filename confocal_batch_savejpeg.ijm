//Created for Frantz Lab confocal files (3-channel Olympus *.oir files) by C. Frantz 2025

//Macro does the following:
//1. Selects image files from an input folder
//2. Saves composite image and individual channels as jpegs


// ====================
// DEFINE VARIABLES
// ====================

// --- Manual Definitions ---
suffix = ".oir";
tlchan = 3;

// --- User Input ---
inputDir = getDirectory("Choose input directory");
outputDir = getDirectory("Choose output directory");

setBatchMode(true);


// =======================
// MAIN LOOP
// =======================

// --- Parse the list of files ---
filelist = getFileList(inputDir);


for (f = 0; f < filelist.length; f++) {

	// --- Check that the file has the correct extension --- 
	file = filelist[f];
	if (!endsWith(file, suffix)) continue;
	
	print("Processing: " + file);
	baseFileName = replace(file, suffix, "");
	
	// --- Open file to create saved composite ---
	run("Bio-Formats Importer", "open=[" + inputDir + file + "] color_mode=Composite view=Hyperstack stack_order=XYCZT");
	compTitle = getTitle();
	run("Scale Bar...", "width=100 height=50 thickness=10 font=25 color=Black bold overlay");
	saveAs("Jpeg", outputDir + baseFileName + "_composite.jpg");
	selectWindow(compTitle);
	close();
	
	// --- Open file for split channels --- 
	run("Bio-Formats Importer", "open=[" + inputDir + file + "] Autoscale color_mode=Default view=Hyperstack stack_order=XYCZT");
	run("Split Channels");

	// --- Save tiff images of each channel ---
	channels = getList("image.titles");

	for (c = 0; c < channels.length; c++) {
		channel = channels[c];
		selectWindow(channel);
		
		// Extract channel number
		chan = -1;
		if (startsWith(channel, "C")) {
			dashIndex = indexOf(channel, "-");
			if (dashIndex > 1) {
				chanStr = substring(channel, 1, dashIndex);
				chan = parseInt(chanStr) - 1;  // convert to 0-based
			}
		}

		// Add appropriate scale bar
		scaleColor = "White";
		if ((chan + 1) == tlchan) {
			scaleColor = "Black";
		}
		run("Scale Bar...", "width=100 height=50 thickness=10 font=25 color=" + scaleColor + " bold overlay");
		
		// Save image
		saveAs("Jpeg", outputDir + baseFileName + "_C" + c + ".jpg");
		close();
	}
	
	// --- Close all other windows ---
    titles = getList("image.titles");
	for (i = 0; i < titles.length; i++) {
		selectWindow(titles[i]);
		close();
	}
	
	
}
	
setBatchMode(false);

print("Done.");