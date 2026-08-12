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

    double tot_tof_edep = 0.0;
    double tot_trk_edep = 0.0;
    
    std::cout << "analyzing..." << std::endl;

    for (Long64_t i = 0; i < nEntries; i++) {

        Instrument_Events->GetEntry(i);

        const auto& energies        = Event->GetTotalEnergyDeposition();
        const auto& volumeIds       = Event->GetVolumeId();
        const auto& eventId         = Event->GetEventId();

        tot_trk_edep = 0.0;
        tot_tof_edep = 0.0;

        for (unsigned int k = 0; k < energies.size(); k++) {
	
            unsigned int vid = volumeIds.at(k);
            double edep      = energies.at(k);

            if(vid >= 200000000) {
                tot_trk_edep += edep;
            }

           else if(vid < 200000000) {
                tot_tof_edep += edep;
            }
        }
        if(tot_tof_edep == 0.0) {
            std::cout<< eventId <<std::endl;
        }
    }
} 
