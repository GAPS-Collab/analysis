#include <TFile.h>
#include "GOptionParser.hh"
#include "GFileIO.hh"
#include "CEventRec.hh"
#include "TChain.h"
#include <format>
#include <boost/format.hpp>
#include <vector>

using std::vector, std::string, std::cout, std::endl;
using boost::format;

int main(int argc, char* argv[]){


    GOptionParser* parser = GOptionParser::GetInstance();
    parser->AddProgramDescription("Produces a histogram of Energy Deposition per paddle over the data given by rec_file for the paddles indicated in the arguments");
    parser->AddCommandLineOption<string>("rec_path", "path to instrument data files", "./*", "i");
    parser->ParseCommandLine(argc, argv);
    parser->Parse();


    string data_path = parser->GetOption<string>("rec_path");
    TChain* Instrument_Events = new TChain("TreeRec");
    Instrument_Events->SetAutoDelete(true);
    CEventRec* Event = new CEventRec;
    Instrument_Events->SetBranchAddress("Rec", &Event);
    Instrument_Events->Add(data_path.c_str());


    Long64_t nEntries = Instrument_Events->GetEntries();
    std::vector<double> tof_edep;
    std::vector<double> trk_edep;

    std::string last_file = "";
    
    std::cout << "analyzing..." << std::endl;

    for (Long64_t i = 0; i < nEntries; i++) {

        Instrument_Events->GetEntry(i);
        TFile* currentFile = Instrument_Events->GetCurrentFile();

        if (currentFile) {
            std::string fname = currentFile->GetName();

            if (fname != last_file) {
                std::cout << "Now reading: " << fname << std::endl;
                last_file = fname;
            }
        }

        const auto& energies        = Event->GetTotalEnergyDeposition();
        const auto& volumeIds       = Event->GetVolumeId();
        const auto& eventId         = Event->GetEventId();

        for (unsigned int k = 0; k < energies.size(); k++) {
	
            unsigned int vid = volumeIds.at(k);
            double edep      = energies.at(k);

            if(vid >= 200000000) {
               trk_edep.push_back(energies[k]);
            }

           else if(vid < 200000000) {
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

            if (max_tracker_edep >= 80.0) {
                std::cout << eventId <<std::endl;
            }
        }
        tof_edep.clear();
        trk_edep.clear(); 
    }
} 
