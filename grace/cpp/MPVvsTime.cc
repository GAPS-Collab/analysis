#include <TFile.h>
#include <TH1D.h>
#include <TGraph.h>
#include <TCanvas.h>
#include <iostream>
#include <vector>
#include <map>
#include <TF1.h>
#include "GOptionParser.hh"
#include <string>

int main(int argc, char* argv[]) {
    
    GOptionParser* parser = GOptionParser::GetInstance();
    parser->AddProgramDescription("produces bar chart of MPVs for 24hr period for each paddle based on 2 hour data chunks");
    parser->AddCommandLineOption<std::string>("date", "Date to use (format: DDMMYY)", "", "d");
    parser->AddCommandLineOption<std::string>("out_path", "path to output root file", ".", "o");
    parser->ParseCommandLine(argc, argv);
    parser->Parse();


    std::string date = parser->GetOption<std::string>("date");
    std::string base_path = "/home/gtytus/analysis/grace/cpp/build/v26.01_edep";

    std::vector<std::string> dirs;
    for (int start = 0; start < 24; start += 1) {
        int end = start + 1;
        std::ostringstream oss;
        oss << base_path << "/" << date << "_1_hr_chunks/" << date << "_" << start << "_" << end;
        dirs.push_back(oss.str());
    }

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


    std::string out_path = parser->GetOption<std::string>("out_path");
    std::string root_name = out_path + "/mpv_vs_time.root";
    TFile* outFile = new TFile(root_name.c_str(), "RECREATE");

    for (auto vid : volume_ids) {

        std::vector<double> times;
        std::vector<double> mpvs;

        for (int i = 0; i < dirs.size(); i++) {

            std::string filename = dirs[i] + "/energy_by_volume.root";
            TFile file(filename.c_str(), "READ");

            if (file.IsZombie()) continue;
            std::cout << "Checking volume " << vid << " in file " << filename << std::endl;

            std::string histname = "Edep_" + std::to_string(vid);
            TH1D* hist = (TH1D*)file.Get(histname.c_str());
            
	    if (!hist) {
    		std::cout << "  Histogram missing: " << histname << std::endl;
    		file.Close();
    		continue;
	    }	


            TF1* fit = hist->GetFunction("landauFit");
		
	    if (!fit) {
    		std::cout << "  Fit missing for " << histname << std::endl;
    		hist->Print();   // shows attached functions
    		file.Close();
    		continue;
	    }

            if (!fit) {
                file.Close();
                continue;
            }

            double mpv = fit->GetParameter(1);

            times.push_back(i * 2.0 + 1.0);
            mpvs.push_back(mpv);

            file.Close();
	    outFile->cd();
        }

        if (mpvs.size() == 0) continue;

        /*TGraph* graph = new TGraph(times.size(), &times[0], &mpvs[0]);
	
	graph->SetName(Form("MPV_%u", vid));
        graph->SetTitle(Form("MPV vs Time for Volume %u", vid));
        graph->GetXaxis()->SetTitle("2-hour bin (0 = 00:00-02:00)");
        graph->GetYaxis()->SetTitle("MPV [MeV]");
	graph->SetMarkerStyle(20);       // solid circle
	graph->SetMarkerSize(1.0);       // make the points larger
	graph->SetLineColor(kMagenta-2);	// line color
	graph->SetLineWidth(2);           // line width
	graph->SetMarkerColor(221);

        graph->Write();


    	TCanvas c;
	graph->Draw("APL");
	c.SaveAs(Form("MPV_%u.pdf", vid));
    		
	delete graph;
	*/

	int nBins = dirs.size(); // 24 bins for 24 time windows
	TH1D* histMPV = new TH1D(Form("MPV_%u", vid),
                         Form("MPV per 1-hour window for volume %u", vid),
                         nBins, 0, nBins);
        std::vector<std::string> binLabels = {
    		"00:00-00:59", "01:00-01:59", "02:00-02:59", "03:00-03:59","04:00-04:59", "05:00-05:59","06:00-06:59", "07:00-07:59","08:00-08:59","09:00-09:59","10:00-10:59",
		"11:00-11:59", "12:00-12:59", "13:00-13:59", "14:00-14:59", "15:00-15:59", "16:00-16:59", "17:00-17:59", "18:00-18:59", "19:00-19:59", "20:00-20:59",
    		"21:00-21:59", "22:00-22:59", "23:00-23:59", "24:00-24:59"
	};

	for (int i = 0; i < nBins; i++) {
    		histMPV->GetXaxis()->SetBinLabel(i+1, binLabels[i].c_str());
	}

	for (int i = 0; i < mpvs.size(); i++) {
            histMPV->SetBinContent(i+1, mpvs[i]); // bin 1 = first 2-hr window
   	}

	// Write to ROOT file
    	outFile->cd();
    	histMPV->Write();
	
	TCanvas c;
	c.SetBottomMargin(0.15);
	histMPV->SetFillColor(kPink+4);
	histMPV->SetBarWidth(0.9);
	histMPV->SetStats(0); // hide statistics box
	histMPV->GetYaxis()->SetTitle("MPV [MeV]");
	histMPV->GetXaxis()->LabelsOption("v"); // rotate labels vertically if crowded
	histMPV->GetYaxis()->SetRangeUser(0.0, 1.5);
	histMPV->Draw("BAR"); // or "BAR0" for gaps between bars
	c.SaveAs(Form("MPV_%u_bar.pdf", vid));	
    	delete histMPV;
    }

    outFile->Close();
    delete outFile;

    std::cout << "Finished MPV extraction.\n";
}
