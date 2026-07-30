#include <vector>
#include <string>
#include <iostream>
#include <fstream>
using std::vector;
using std::string;
using std::cout;
using std::cerr;
using std::endl;
#include <map>
#include <TFile.h>
#include <TTree.h>
#include <TChain.h>
#include "CEventRec.hh"
#include "GGeometryObject.hh"


int main(int argc, char* argv[]) {
    std::ifstream infile("/home/gtytus/analysis/grace/cpp/build/26.03_files.txt");
    std::string fname;
    int n_files = 0;

    if (!infile.is_open()) {
        std::cerr << "Failed to open root_files.txt" << std::endl;
        return 1;
    }
    TFile* fout = new TFile("track_edep.root", "RECREATE", "", 4);
    TTree* tree = new TTree("tracks", "Selected track hit information");

    float edep;
    float step_length;
    int volume_id;
    uint64_t timestamp;

    tree->Branch("edep", &edep);
    tree->Branch("step_length", &step_length);
    tree->Branch("volume_id", &volume_id);
    tree->Branch("timestamp", &timestamp);

    TChain* Instrument_Events = new TChain("TreeRec");
    Instrument_Events->SetAutoDelete(true);
    CEventRec* Event = nullptr;
    Instrument_Events->SetBranchAddress("Rec", &Event);

    while (std::getline(infile, fname)) {
        Instrument_Events->Add(fname.c_str());
        n_files++;
    }
    std::cout << "Added " << n_files << " files" << std::endl;
    std::cout << "Starting event loop..." << std::endl;

    size_t nentries = Instrument_Events->GetEntries();

    std::cout << "Starting event loop over "<< nentries << " entries" << endl;

    for (size_t i = 0; i < nentries; i++) {
        Instrument_Events->GetEntry(i);

        if (i == 0)
            std::cout << "About to read first entry" << std::endl;

        Instrument_Events->GetEntry(i);

        if (i == 0) {
            std::cout << "First entry read successfully" << std::endl;
        }

        if (i % 100000 == 0) {
            cout << i << " / " << nentries << endl;
	    }
        
        timestamp = Event->GetEventTime();


        if (Event->GetPrimaryBeta() < 0.8)
            continue;

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

        timestamp = Event->GetEventTime();

        const auto& track_edeps = primaryTrack->GetEnergyDeposition();
        const auto& track_steps = primaryTrack->GetStepLength();

        if (volids.size() != track_edeps.size() ||
            volids.size() != track_steps.size()) {
        
            std::cerr << "Size mismatch!\n";
            std::cerr << "volids = " << volids.size()
                    << " edeps = " << track_edeps.size()
                    << " steps = " << track_steps.size()
                    << std::endl;
            continue;
        }


        for (size_t k = 0; k < volids.size(); k++) {

            const double tof_thickness = 0.635; //cm
            const double tracker_thickness = 0.23; //cm

            if (!GGeometryObject::IsTofVolume(volids[k]))
                continue;

            if(GGeometryObject::IsUmbrellaVolume(volids[k])) {
                if(GGeometryObject::IsCortinaVolume(volids[k])) {
                    if(Event->GetPrimaryBeta() > 0.8 && Event->GetPrimaryBeta() < 1.2) step_length = tof_thickness / sqrt(1-pow(Event->GetPrimaryMomentumDirection().CosTheta(),2)); //cortina side panels
                }

                else {
                    if(Event->GetPrimaryBeta() > 0.8 && Event->GetPrimaryBeta() < 1.2) step_length = tof_thickness / fabs(Event->GetPrimaryMomentumDirection().CosTheta()); //umbrella panels
                }
            }

            else if(GGeometryObject::IsCubeVolume(volids[k])) {
                int Face = GGeometryObject::GetTofFace(volids[k]);
                if(Face == 0 || Face == 1) { //cube top and bot
                    if(Event->GetPrimaryBeta() > 0.8 && Event->GetPrimaryBeta() < 1.2) step_length = tof_thickness / fabs(Event->GetPrimaryMomentumDirection().CosTheta());
                }

                else if(Face == 2 || Face == 3) { //cube front and back
                    if(Event->GetPrimaryBeta() > 0.8 && Event->GetPrimaryBeta() < 1.2) step_length = tof_thickness / sqrt(1-pow(Event->GetPrimaryMomentumDirection().CosTheta(),2));
                }

                else if(Face == 4 || Face == 5) { //cube left and right
                    if(Event->GetPrimaryBeta() > 0.8 && Event->GetPrimaryBeta() < 1.2) step_length = tof_thickness / sqrt(1-pow(Event->GetPrimaryMomentumDirection().CosTheta(),2));
                }
            }

            ///else {
                ///if(Event->GetPrimaryBeta() > 0.8 && Event->GetPrimaryBeta() < 1.2) step_length = tracker_thickness / fabs(Event->GetPrimaryMomentumDirection().CosTheta());
            ///}

            edep = track_edeps[k];
            //step_length = track_steps[k];
            volume_id = volids[k];
        
            tree->Fill();
        }
    }
    fout->Write();
    fout->Close();
}
