#include <TFile.h>
#include "GOptionParser.hh"
#include "GFileIO.hh"
#include "CEventRec.hh"
#include "TChain.h"
#include <vector>
#include <format>
#include <TH1D.h>
#include "TCanvas.h"
#include "TStyle.h"

/*
A script which reads in reconstructed hits for TOF and Tracker, and if the TOF hit is within a set window,
computes the differnce between the highest valued TOF hit in the event and the highest valued Tracker hit
in the event. Produces a TH1D of the difference called high_edep_tof_trk.pdf
*/

using std::vector, std::string, std::cout, std::endl;

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

    Long64_t nEntries = Instrument_Events->GetEntries();

    string out_path = parser->GetOption<string>("out_path");
    if (out_path.back() != '/')
    out_path += "/";

    TH1D* h_diff = new TH1D("h_diff", "TOF - Tracker Max Energy;E_{TOF} - E_{TRK} [MeV];Counts", 
                       100, -100, 100);

    std::cout << "analyzing..." << std::endl;

    for (Long64_t i = 0; i < nEntries; i++) {

        Instrument_Events->GetEntry(i);

        const auto& energies        = Event->GetTotalEnergyDeposition();
        const auto& volumeIds       = Event->GetVolumeId();

        std::vector<double> tof_edep;
        std::vector<double> trk_edep;

        for (unsigned int k = 0; k < energies.size(); k++) {
	
            unsigned int vid = volumeIds.at(k);
            double edep      = energies.at(k);
            
            if(vid >= 200000000) {
                trk_edep.push_back(energies[k]);
            }
            else {
                tof_edep.push_back(energies[k]);
            }
        }

        double low = 20.0;
        double high = 27.0;

        bool tof_in_range = std::any_of(tof_edep.begin(), tof_edep.end(),
            [low, high](double e) {
                return e >= low && e <= high;
            });

        if (tof_in_range && !trk_edep.empty()) {
            auto max_it = std::max_element(trk_edep.begin(), trk_edep.end());
            double max_tracker_edep = *max_it;
            
            auto max_id = std::max_element(tof_edep.begin(), tof_edep.end());
            double max_tof_edep = *max_id;

            double diff_tof_trk = max_tof_edep - max_tracker_edep;
            h_diff->Fill(diff_tof_trk);
        }   
        tof_edep.clear();
        trk_edep.clear();  
    }
    TCanvas* c1 = new TCanvas("c","c",800,600);
    c1->cd();
    h_diff->GetXaxis()->SetRangeUser(-100.0, 30.0);
    gStyle->SetStatY(0.875);
    gStyle->SetStatX(0.35);
    h_diff->Draw();
    gPad->Update();
    
    std::string pdf_name = out_path + "high_edep_tof_trk.pdf";
    c1->SaveAs(pdf_name.c_str());
} 