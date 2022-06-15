//Maya ASCII 2020 scene
//Name: dropshape_twosided_template.ma
//Last modified: Tue, May 31, 2022 08:16:07 PM
//Codeset: 1252
requires maya "2020";
createNode transform -n "dropshape_twosided_template";
	rename -uid "A5314857-459D-CC99-54E5-1DBF40490182";
createNode nurbsCurve -n "dropshape_twosided_templateShape" -p "dropshape_twosided_template";
	rename -uid "84CE2F9E-4A4B-E2C1-2C4B-BA8D26F1D995";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 12 2 no 3
		17 -2 -1 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
		15
		-0.290585068993235 0.024236280400766107 -1.1102230246251565e-16
		-0.46513289569184046 -1.38326315013802e-16 1.4432899320127035e-15
		-0.29058506899323644 -0.0242362804007661 -4.4408920985006262e-16
		-0.14479168227193076 -0.20325144128145717 -8.8817841970012523e-16
		-2.4980018054066022e-16 -0.24318553913847624 -8.8817841970012523e-16
		0.14479168227193104 -0.20325144128145745 -1.2212453270876722e-15
		0.29058506899323555 -0.0242362804007661 -1.4432899320127035e-15
		0.46513289569184046 -2.2289036013233836e-16 -4.4408920985006262e-16
		0.29058506899323733 0.024236280400765961 -9.9920072216264089e-16
		0.14479168227193126 0.203251441281457 -7.7715611723760958e-16
		1.0824674490095276e-15 0.24318553913847624 -6.9388939039072284e-16
		-0.14479168227193065 0.20325144128145733 -4.4408920985006262e-16
		-0.290585068993235 0.024236280400766107 -1.1102230246251565e-16
		-0.46513289569184046 -1.38326315013802e-16 1.4432899320127035e-15
		-0.29058506899323644 -0.0242362804007661 -4.4408920985006262e-16
		;
// End of dropshape_twosided_template.ma
