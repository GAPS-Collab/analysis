#include <TFile.h>
#include <TTree.h>
#include <TChain.h>
#include <TH1D.h>
#include <TCanvas.h>
#include <TPaveText.h>
#include <TText.h>
#include <TF1.h>
#include <TLine.h>
#include <cmath>
#include <numeric>
#include <vector>
#include <string>
#include <iostream>
#include <boost/format.hpp>
#include "GOptionParser.hh"
#include "CEventRec.hh"
#include "GRecoHit.hh"
#include "GGeometryObject.hh"
#include "progressbar.hpp"
#include <TStyle.h>
#include <TLegend.h>
#include <TLatex.h>
#include <filesystem>

using std::vector;
using std::string;
using std::cout;
using std::endl;
using boost::format;

int main(int argc, char* argv[]) {
    GOptionParser* parser = GOptionParser::GetInstance();
    parser->AddProgramDescription("plots the primary beta distribution");
    parser->AddCommandLineOption<string>("rec_path", "path to instrument data files", "./*", "i");
    parser->ParseCommandLine(argc, argv);
    parser->Parse();

    string data_path = parser->GetOption<string>("rec_path");

    TChain* Instrument_Events = new TChain("TreeRec");
        Instrument_Events->SetAutoDelete(true);
        CEventRec* Event = nullptr;
        Instrument_Events->SetBranchAddress("Rec", &Event);
        Instrument_Events->Add(data_path.c_str()); 


    TFile *outfile = new TFile("primary_beta.root", "RECREATE");
    TH1D *h_beta = new TH1D(
        "h_beta",
        "Primary #beta;Primary #beta;Events",
        200, 0.0, 1.5
    );

    size_t nentries = Instrument_Events->GetEntries();

    for (size_t i = 0; i < nentries; i++) {
        Instrument_Events->GetEntry(i);

        if (i % 100000 == 0) {
            cout << i << " / " << nentries << endl;
        }

        bool hasFindPrimary = false;

        for (const auto& type : Event->ListAvailableReconstructions()) {
            if (type == "FindPrimary") {
                hasFindPrimary = true;
                break;
            }
        }

        if (!hasFindPrimary)
            continue;

        Event->ChooseReconstruction("FindPrimary");

        decltype(Event->GetTrack(0)) primaryTrack = nullptr;

        for (int j = 0; j < Event->GetNTracks(); ++j) {
            auto* track = Event->GetTrack(j);
            if (track->IsPrimary()) {
                primaryTrack = track;
                break;
            }
        }

        if (!primaryTrack)
            continue;  // No primary track found

        if (primaryTrack->GetChi2() > 3.2)
            continue;

        const auto& volids = primaryTrack->GetVolumeId();

        bool has_inner = false;
        bool has_outer = false;

        int ntof = 0;

        for (size_t k = 0; k < volids.size(); k++) {

            int volid = volids[k];

            if (!GGeometryObject::IsTofVolume(volid))
                continue;

            ntof++;

            if (GGeometryObject::IsCubeVolume(volid))
                has_inner = true;

            if (GGeometryObject::IsUmbrellaVolume(volid))
                has_outer = true;
        }

        if (ntof < 3)
            continue;

        if (!(has_inner && has_outer))
        continue;


        double beta = Event->GetPrimaryBeta();
        h_beta->Fill(beta);
    }

    // Draw histogram
    TCanvas *c = new TCanvas("c", "Primary Beta", 800, 600);
    h_beta->Draw();
    h_beta->Write();
    c->SaveAs("primary_beta.png");
    outfile->Close();
    delete outfile;
    delete c;
}