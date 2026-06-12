#include <vector>
#include <string>
#include <iostream>
using std::vector;
using std::string;
using std::cout;
using std::cerr;
using std::endl;
#include <map>
#include <TFile.h>
#include <TTree.h>
#include <TChain.h>
#include "GOptionParser.hh"
#include "CEventRec.hh"
#include "GGeometryObject.hh"

std::vector<int> panel_1_vids  = {110000000, 110000100, 110000200, 110000300, 110000400, 110000500, 110000600, 110000700, 110000800, 110000900, 110001000, 110001100};
std::vector<int> panel_2a_vids = {111000000, 111000100, 111000200, 111000300, 111000400, 111000500};
std::vector<int> panel_2b_vids = {111000700, 111000800, 111000900, 111001000};
std::vector<int> panel_3_vids  = {112000700, 112000600, 112000500, 112000400, 112000300, 112000200, 112000100, 112000000};
std::vector<int> panel_4_vids  = {114000700, 114000600, 114000500, 114000400, 114000300, 114000200, 114000100, 114000000};
std::vector<int> panel_5a_vids = {113000700, 113000600, 113000500};
std::vector<int> panel_5b_vids = {113000200, 113000100, 113000000};
std::vector<int> panel_6_vids  = {115000000, 115000100, 115000200, 115000300, 115000400, 115000500, 115000600, 115000700};
std::vector<int> panel_57_vids = {116000000};
std::vector<int> panel_58_vids = {116200000};
std::vector<int> panel_59_vids = {116300000};
std::vector<int> panel_60_vids = {116100000};
std::vector<int> panel_7_vids  = {100000000, 100000100, 100000200, 100000300, 100000400, 100000500, 100000600, 100000700, 100000800, 100000900, 100001000, 100001100};
std::vector<int> panel_8_vids  = {100300500, 100300400, 100300300, 100300200, 100300100, 100300000};
std::vector<int> panel_9_vids  = {100200500, 100200400, 100200300, 100200200, 100200100, 100200000};
std::vector<int> panel_10_vids = {100400000, 100400100, 100400200, 100400300, 100400400, 100400500};
std::vector<int> panel_11_vids = {100600500, 100600400, 100600300, 100600200, 100600100, 100600000};
std::vector<int> panel_12_vids = {100100400, 100100300, 100100200, 100100100, 100100000};
std::vector<int> panel_13_vids = {100500500, 100500400, 100500300, 100500200, 100500100, 100500000};
std::vector<int> panel_14_vids = {102000900, 102000800, 102000700, 102000600, 102000500, 102000400, 102000300, 102000200, 102000100, 102000000};
std::vector<int> panel_15_vids = {104000000, 104000100, 104000200, 104000300, 104000400, 104000500, 104000600, 104000700, 104000800, 104000900};
std::vector<int> panel_16_vids = {103000900, 103000800, 103000700, 103000600, 103000500, 103000400, 103000300, 103000200, 103000100, 103000000};
std::vector<int> panel_17_vids = {105000900, 105000800, 105000700, 105000600, 105000500, 105000400, 105000300, 105000200, 105000100, 105000000};
std::vector<int> panel_18_vids = {106000200, 106000100, 106000000};
std::vector<int> panel_19_vids = {106200000, 106200100, 106200200};
std::vector<int> panel_20_vids = {106300000, 106300100, 106300200};
std::vector<int> panel_21_vids = {106100200, 106100100, 106100000};

int main(int argc, char* argv[]) {
    GOptionParser* parser = GOptionParser::GetInstance();
    parser->AddProgramDescription("Computes the panel to panel timing offsets for TOF panels");
    parser->AddCommandLineOption<string>("rec_path", "path to instrument data files", "./*", "i");
    parser->ParseCommandLine(argc, argv);
    parser->Parse();

    string data_path = parser->GetOption<string>("rec_path");

    struct PanelInfo {
        int panel;
    };

    std::map<int, PanelInfo> volid_lookup;
    auto add_panel_mapping = [&](int panel_num, const std::vector<int>& vids) {
        for (size_t idx = 0; idx < vids.size(); ++idx) {
        volid_lookup[vids[idx]] =
            {panel_num};
        }
    };

    add_panel_mapping(1, panel_1_vids);
    add_panel_mapping(2, panel_2a_vids);
    add_panel_mapping(22, panel_2b_vids);
    add_panel_mapping(3, panel_3_vids);
    add_panel_mapping(4, panel_4_vids);
    add_panel_mapping(5, panel_5a_vids);
    add_panel_mapping(55, panel_5b_vids);
    add_panel_mapping(6, panel_6_vids);
    add_panel_mapping(7, panel_7_vids);
    add_panel_mapping(8, panel_8_vids);
    add_panel_mapping(9, panel_9_vids);
    add_panel_mapping(10, panel_10_vids);
    add_panel_mapping(11, panel_11_vids);
    add_panel_mapping(12, panel_12_vids);
    add_panel_mapping(13, panel_13_vids);
    add_panel_mapping(14, panel_14_vids);
    add_panel_mapping(15, panel_15_vids);
    add_panel_mapping(16, panel_16_vids);
    add_panel_mapping(17, panel_17_vids);
    add_panel_mapping(18, panel_18_vids);
    add_panel_mapping(19, panel_19_vids);
    add_panel_mapping(20, panel_20_vids);
    add_panel_mapping(21, panel_21_vids);
    add_panel_mapping(57, panel_57_vids);
    add_panel_mapping(58, panel_58_vids);
    add_panel_mapping(59, panel_59_vids);
    add_panel_mapping(60, panel_60_vids);

    TFile* fout = new TFile("track_edep.root", "RECREATE");
    TTree* tree = new TTree("tracks", "Selected track hit information");

    std::vector<float> edeps;
    std::vector<float> step_lengths;
    std::vector<int> volume_ids;
    std::vector<int> panel_ids;
    uint64_t timestamp;
    int event_number;

    tree->Branch("edep", &edeps);
    tree->Branch("step_length", &step_lengths);
    tree->Branch("volume_id", &volume_ids);
    tree->Branch("panel", &panel_ids);
    tree->Branch("timestamp", &timestamp);
    tree->Branch("event_number", &event_number);

    TChain* Instrument_Events = new TChain("TreeRec");
    Instrument_Events->SetAutoDelete(true);
    CEventRec* Event = new CEventRec;
    Instrument_Events->SetBranchAddress("Rec", &Event);
    Instrument_Events->Add(data_path.c_str()); 

	std::cout << "Starting event loop..." << std::endl;

    for (size_t i = 0; i < Instrument_Events->GetEntries(); i++) {
        Instrument_Events->GetEntry(i);
        
        timestamp = Event->GetEventTime();
        if (Event->GetPrimaryBeta() < 0.8)
            continue;

        for (int j = 0; j < Event->GetNTracks(); j++) {
            auto* track = Event->GetTrack(j);

            if (track->GetChi2() > 3.2)
                continue;

            auto volids = track->GetVolumeId();

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
            event_number = Event->GetEventId();
            edeps.clear();
            step_lengths.clear();
            volume_ids.clear();
            panel_ids.clear();

            const auto& track_edeps = track->GetEnergyDeposition();
            const auto& track_steps = track->GetStepLength();

            for (size_t k = 0; k < volids.size(); k++) {
                if (!GGeometryObject::IsTofVolume(volids[k]))
                    continue;

                edeps.push_back(track_edeps[k]);
                step_lengths.push_back(track_steps[k]);
                volume_ids.push_back(volids[k]);

                auto it = volid_lookup.find(volids[k]);

                if (it != volid_lookup.end()) {
                    panel_ids.push_back(it->second.panel);
                }
                else {
                    panel_ids.push_back(-1);
                }
            }
            tree->Fill();
        }
    }    
    fout->Write();
    fout->Close();
}