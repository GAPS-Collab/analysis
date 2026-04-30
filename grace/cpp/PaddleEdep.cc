#include <TFile.h>
#include "CEventMc.hh"
#include "GOptionParser.hh"
#include "GFileIO.hh"
#include "CEventRec.hh"
#include "GGeometryObject.hh"
#include "TChain.h"
#include "TH1.h"
#include "TH2.h"
#include "TH3.h"
#include "TCanvas.h"
#include <algorithm>
#include <iostream>
#include <vector>
#include "TGraph.h"
#include "TColor.h"
#include "TStyle.h"
#include <format>
#include <boost/format.hpp>
#include <TH1.h>
#include <TF1.h>
#include <TPaveText.h>
#include "TFile.h"
#include <TLine.h>

using std::vector, std::string, std::cout, std::endl;
using boost::format;

std::vector<unsigned int> volume_ids = {
    110000000,110000100,110000200,110000300,110000400,110000500,110000600,110000700,
    110000800,110000900,110001000,110001100,111001100,111001000,111000900,111000800,
    111000700,111000600,111000500,111000400,111000300,111000200,111000100,111000000,
    112000700,112000600,112000500,112000400,112000300,112000200,112000100,112000000,
    114000700,114000600,114000500,114000400,114000300,114000200,114000100,114000000,
    113000700,113000600,113000500,113000400,113000300,113000200,113000100,113000000,
    115000000,115000100,115000200,115000300,115000400,115000500,115000600,115000700,
    116000000,116200000,116300000,116100000,
    100000000,100000100,100000200,100000300,100000400,100000500,100000600,100000700,
    100000800,100000900,100001000,100001100,
    100300500,100300400,100300300,100300200,100300100,100300000,
    100200500,100200400,100200300,100200200,100200100,100200000,
    100400000,100400100,100400200,100400300,100400400,100400500,
    100600500,100600400,100600300,100600200,100600100,100600000,
    100100500,100100400,100100300,100100200,100100100,100100000,
    100500500,100500400,100500300,100500200,100500100,100500000,
    102000900,102000800,102000700,102000600,102000500,102000400,
    102000300,102000200,102000100,102000000,
    104000000,104000100,104000200,104000300,104000400,104000500,
    104000600,104000700,104000800,104000900,
    103000900,103000800,103000700,103000600,103000500,103000400,
    103000300,103000200,103000100,103000000,
    105000900,105000800,105000700,105000600,105000500,105000400,
    105000300,105000200,105000100,105000000,
    106000200,106000100,106000000,
    106200000,106200100,106200200,
    106300000,106300100,106300200,
    106100200,106100100,106100000
    };

int main(int argc, char* argv[]){


    GOptionParser* parser = GOptionParser::GetInstance();
    parser->AddProgramDescription("Produces a histogram of Energy Deposition per paddle over the data given by rec_file for the paddles indicated in the arguments");
    parser->AddCommandLineOption<string>("rec_path", "path to instrument data files", "./*", "i");
    parser->AddCommandLineOption<string>("out_path", "path to output directory", "./*", "o");
    parser->ParseCommandLine(argc, argv);
    parser->Parse();


    string data_path = parser->GetOption<string>("rec_path");
    TChain* Instrument_Events = new TChain("TreeRec");
    Instrument_Events->SetAutoDelete(true);
    CEventRec* Event = new CEventRec;
    Instrument_Events->SetBranchAddress("Rec", &Event);
    Instrument_Events->Add(data_path.c_str());

    std::unordered_map<unsigned int, TH1D*> energy_hists;

    string out_path = parser->GetOption<string>("out_path");
    if (out_path.back() != '/')
    out_path += "/";

    for (auto vid : volume_ids) {

        std::string name  = "Edep_" + std::to_string(vid);
        std::string title = "Energy Deposition for Volume " + std::to_string(vid);

        energy_hists[vid] = new TH1D(
            name.c_str(),
            title.c_str(),
            100,        // bins
            0.0, 25.0   // energy range
        );
	
	    energy_hists[vid]->SetStats(0);
        energy_hists[vid]->SetDirectory(nullptr);
        energy_hists[vid]->GetXaxis()->SetTitle("Energy Deposition [MeV]");
        energy_hists[vid]->GetYaxis()->SetTitle("Counts");
    }

    Long64_t nEntries = Instrument_Events->GetEntries();
    std::cout << "analyzing..." << std::endl;

    for (Long64_t i = 0; i < nEntries; i++) {

        Instrument_Events->GetEntry(i);

        const auto& energies        = Event->GetTotalEnergyDeposition();
        const auto& volumeIds       = Event->GetVolumeId();
	    const auto& triggerSources  = Event->GetTriggerSources();

        for (unsigned int k = 0; k < energies.size(); k++) {
	
            unsigned int vid = volumeIds.at(k);
            double edep      = energies.at(k);
	    
	        if (energy_hists.count(vid)) {
                energy_hists[vid]->Fill(edep);
            }
        }
    }

    TCanvas* canvas = new TCanvas("c","c",800,600);

    for (auto& pair : energy_hists) {
	TH1D* hist = pair.second;
	
	if (!hist) {
        std::cout << "  Histogram missing: " << std::endl;
        continue;
    }

	if (hist->GetEntries() < 10) {
		std::cout<< "Too few entries for fit" << std::endl;
	}

    canvas->cd();
	// finding FWHM
	int maxBin = hist->GetMaximumBin();
	double maxContent = hist->GetBinContent(maxBin);
	double halfMax = 0.5 * maxContent;
	
	int leftBin = maxBin;
	while (leftBin > 1 && hist->GetBinContent(leftBin) > halfMax) {
    	leftBin--;
	}

	int rightBin = maxBin;
	int nBins = hist->GetNbinsX();
	while (rightBin < nBins && hist->GetBinContent(rightBin) > halfMax) {
    	rightBin++;
	}

	if (rightBin <= leftBin) continue; //in case fit fails it will still plot

	// FWHM window 
	double fitMin = hist->GetBinLowEdge(leftBin);
	double fitMax = hist->GetBinLowEdge(rightBin + 1);	
		
	// Landau Fit
	TF1* landauFit = new TF1("landauFit", "landau", 0.0, 25.0);
	// initial parameters (maximum, MPV, width)
	landauFit->SetRange(fitMin, fitMax);
	landauFit ->SetParameters(maxContent, hist->GetBinCenter(maxBin), 0.3);
    landauFit->SetNpx(2000);
	hist->Fit(landauFit, "RQ0", "", fitMin, fitMax);
	landauFit->SetRange(0.0, 25.0);

	hist->Draw();
	landauFit->Draw("same");	
	
	// TPaveText
	double entries = hist->GetEntries();
    double mpv     = landauFit->GetParameter(1);
    double width   = landauFit->GetParameter(2);
    double chi2    = landauFit->GetChisquare();
    int ndf        = landauFit->GetNDF();

	TPaveText* box = new TPaveText(0.6,0.65,0.88,0.88,"NDC");
    box->SetFillColor(0);
    box->SetBorderSize(1);
    box->SetTextAlign(12);
    box->SetTextSize(0.03);
    box->AddText(Form("Entries = %.0f", entries));
    box->AddText(Form("MPV = %.3f MeV", mpv));
    box->AddText(Form("Width = %.3f", width));
    box->AddText(Form("#chi^{2}/NDF = %.2f", chi2/ndf));
    box->Draw();
        
	// save files for pdf and canvas
	std::string pdf_name = out_path + "Edep_" + std::to_string(pair.first) + ".pdf";
    canvas->SaveAs(pdf_name.c_str());
	
	// save root files
	std::string root_name = out_path + "/energy_by_volume.root";
	TFile outfile(root_name.c_str(), "RECREATE");

	for (auto& pair : energy_hists) {
    	pair.second->Write();   // now includes fit
    }   

	outfile.Close();

	// cleanup
	delete landauFit;
	delete box;
    }

    delete canvas;
    for (auto& pair : energy_hists) {
        delete pair.second;
    }

    delete Instrument_Events;
    delete Event;

    std::cout << "Done.\n";

    return 0;
}
