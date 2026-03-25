#include <TFile.h>
#include <TH1D.h>
#include <TCanvas.h>
#include <TLine.h>
#include <TDirectory.h>
#include <iostream>
#include <vector>
#include <string>
#include <TLegend.h>
#include <TGraph.h>
#include <TStyle.h>
#include <TAxis.h>
#include <TLatex.h>

int main() {

    std::string base_path = "/home/gtytus/analysis/grace/cpp/build/v25.10_edep/";

    std::vector<std::string> days = {
        "251216_2_hr_chunks",
	"251217_2_hr_chunks",
        "251218_2_hr_chunks",
        "251219_2_hr_chunks",
        "251220_2_hr_chunks",
        "251221_2_hr_chunks",
        "251222_2_hr_chunks",
	"251223_2_hr_chunks",
	"251224_2_hr_chunks",
	"251225_2_hr_chunks",
	"251226_2_hr_chunks",
	"251227_2_hr_chunks",
	"251228_2_hr_chunks",
	"251229_2_hr_chunks",
	"251230_2_hr_chunks", 
	"251231_2_hr_chunks",
	"260101_2_hr_chunks",
	"260102_2_hr_chunks",
	"260103_2_hr_chunks", 
	"260104_2_hr_chunks", 
	"260105_2_hr_chunks",
	"260106_2_hr_chunks", 
	"260107_2_hr_chunks",
	"260108_2_hr_chunks",
	"260109_2_hr_chunks"
    };

    std::vector<unsigned int> volume_ids = {
    	111000500,100000800,110000400,114000300,112000300,113000200,100200300,102000100,104000800,103000100,105000300,106100200,116000000
    
    };

    std::vector<TFile*> files;

    for (const auto& day : days) {
        std::string path = base_path + day + "/mpv_vs_time.root";
        TFile* f = TFile::Open(path.c_str(), "READ");

        if (!f || f->IsZombie()) {
            std::cout << "WARNING: could not open " << path << std::endl;
            files.push_back(nullptr);
        } else {
            files.push_back(f);
        }
    }

    TH1D* example = nullptr;

    for (auto* f : files) {
        if (!f) continue;
        example = (TH1D*)f->Get(Form("MPV_%u", volume_ids[0]));
        if (example) break;
    }

    if (!example) {
        std::cout << "ERROR: Could not find example histogram." << std::endl;
        return 1;
    }

    int bins_per_day = example->GetNbinsX();
    int total_bins   = bins_per_day * days.size();

    TFile* outFile = new TFile("combined_mpv_vs_time.root", "RECREATE");
    TDirectory* volDir = outFile->mkdir("volumes");

    gStyle->SetOptStat(0);
    gStyle->SetLabelOffset(0.01);
    gStyle->SetLabelSize(0.03);
    gStyle->SetLabelOffset(0.03, "X");
    gStyle->SetLabelSize(0.03, "X");

    TDatime start_time(2025,12,16,0,0,0);
    double t0 = start_time.Convert();


    for (auto volume_id : volume_ids) {
        
	TH1D* combined = new TH1D(
            Form("MPV_%u_combined", volume_id),
            Form("MPV vs Time Volume %u", volume_id),
            total_bins,
            0,
            total_bins
        );

        int global_bin = 1;

        for (size_t d = 0; d < files.size(); d++) {

            TH1D* h = nullptr;
            if (files[d])
                h = (TH1D*)files[d]->Get(Form("MPV_%u", volume_id));

            for (int b = 1; b <= bins_per_day; b++) {

                double value = 0.0;
                if (h)
                    value = h->GetBinContent(b);

                combined->SetBinContent(global_bin, value);
                global_bin++;
            }
        }

        int n = combined->GetNbinsX();
	TGraph* gr = new TGraph(n);

	double seconds_per_bin = 2 * 3600;  
	double seconds_per_day = 24 * 3600;

	for (int i = 1; i <= n; i++) {

    		double x = t0 + (i-1)*seconds_per_bin;
    		double y = combined->GetBinContent(i);

    		gr->SetPoint(i-1, x, y);
	}	

	gr->GetXaxis()->SetTimeDisplay(1);
        gr->GetXaxis()->SetTimeFormat("%m-%d");
	gr->GetXaxis()->SetTitle("Flight Date");
	gr->GetXaxis()->SetTitleOffset(1.8);
	gr->GetXaxis()->SetNdivisions(days.size(), false);

	gr->SetTitle(Form("MPV vs Time Volume %u", volume_id));
	gr->SetMarkerStyle(20);
	gr->SetMarkerSize(0.6);
	
	double sum = 0;
	int count = 0;

	for (int i = 1; i <= combined->GetNbinsX(); i++) {

    		double val = combined->GetBinContent(i);

    		if (val > 0) {   // optional: skip empty bins
        		sum += val;
        		count++;
    		}
	}	

	double mean = sum / count;

	TCanvas* c = new TCanvas(Form("c_%u", volume_id), "", 1200, 600);
	
	gr->Draw("AP");
        double xmin = t0;
	double xmax = t0 + days.size() * seconds_per_day;
	gr->GetXaxis()->SetLimits(xmin, xmax);	

    	gr->GetYaxis()->SetTitle("MPV");
	
	gr->GetYaxis()->SetRangeUser(0, 2.0);
	gr->GetXaxis()->SetLabelSize(0.00);

	gPad->SetBottomMargin(0.15);

	TLine* mean_line = new TLine(xmin, mean, xmax, mean);

	mean_line->SetLineColor(kRed);
	mean_line->SetLineWidth(2);
	mean_line->SetLineStyle(2);
	mean_line->Draw("SAME");
	

	TLegend* leg = new TLegend(0.75,0.8,0.9,0.9);
	leg->AddEntry(gr,"MPV values","p");
	leg->AddEntry(mean_line,Form("Mean = %.2f",mean),"l");
	
	leg->Draw();

	double ymin = gr->GetYaxis()->GetXmin();
	double ymax = gr->GetYaxis()->GetXmax();
	
	for (size_t d = 0; d < days.size(); d++) {
    		double x = t0 + d * seconds_per_day;
		TDatime dt(x);
    		std::string date_label = Form("%02d-%02d", dt.GetMonth(), dt.GetDay());

    		TLatex *label = new TLatex(x, ymin - 0.1, date_label.c_str());
    		label->SetTextAngle(45);   // rotate 90 degrees
    		label->SetTextAlign(22);   // centered horizontally
    		label->SetTextSize(0.03);
    		label->Draw("SAME");
	}		

	for (size_t d = 1; d < days.size(); d++) {
		double x = t0 + d * seconds_per_day;
		TLine* line = new TLine(x, ymin, x, ymax);
    		line->SetLineStyle(2);
    		line->SetLineColor(kGray+2);
    		line->Draw("SAME");	
	}

        volDir->cd();
        gr->Write(Form("mpv_vs_time_vol_%u", volume_id));
        c->Write();
        c->SaveAs(Form("MPV_%u_combined.pdf", volume_id));

        delete c;
        delete combined;
	delete gr;
        delete mean_line;
	delete leg;	
    }

    outFile->Close();
	
    for (auto* f : files)
        if (f) f->Close();

    std::cout << "Done." << std::endl;

    return 0;
}
