
import os
import subprocess

class LaTeX:

    def __init__(self, filename, title, date, quiet=False):

        self.filename = filename

        self.date = date
        self.title = title

        self.quiet = quiet

        self.fed = open(filename,'wt')

        self._write_header()

        
    def _write_header(self):
        
        self.fed.write(
            "\\documentclass[11pt,a4paper]{article}\n"\
            "\n"\
            "\\usepackage[a4paper,headheight=14pt,left=1cm,right=1cm,top=2cm,bottom=2cm]{geometry}\n"\
            "\\usepackage{longtable}\n"\
            "\\usepackage{booktabs}\n"\
            "\\usepackage{multirow}\n"\
            "\\usepackage{fancyhdr}\n"\
            "\\usepackage{pdflscape}\n"\
            "\\usepackage[hidelinks]{hyperref}\n"\
            "\\fancyhead{}\n"\
            "\\fancyfoot{}\n"\
            "\\fancyhead[L]{%s}\n"\
            "\\fancyhead[R]{%s \\rightmark}\n"\
            "\\fancyfoot[C] {-~\\thepage~-}\n"\
            "\\renewcommand{\\headrulewidth}{0.4pt}\n"\
            "\\renewcommand{\\footrulewidth}{0.0pt}\n"\
            "\n"\
            "\\setlength{\\parskip}{0pt}\n"\
            "\\setlength{\\parindent}{0pt}\n"\
            "\n"\
            "\\renewcommand\\contentsname{Results Summary}\n"\
            "\\pagestyle{fancy}\n"\
            "\\begin{document}\n\n"\
            "\\tableofcontents\n\n" % (self.title, self.date))

    def clearpage(self):
        self.write("\\clearpage\n")

    def newpage(self):
        self.write("\\newpage\n")

    def write(self, text):

        self.fed.write(text)

    def add_section_title(self, title, intoc=True):

        self.write("\\section*{%s}\n" % title)
        self.write("\\markright{%s}\n" % title)
        if intoc:
            self.write("\\addcontentsline{toc}{section}{\\protect\\numberline{}%s}\n" % title)

    def totals_table(self, data):

        self.fed.write(
            "\\begin{longtable}[c]{%s}\n"\
            % ("c" + "lccc"))

        self.fed.write("\\toprule\n")
        
        self.fed.write("Rank & Athlete & C1 & K1 & Avg \\\\\n ")

        self.fed.write("\\midrule\n")
        self.fed.write("\\endhead\n")

        for line in data:
            assert len(line) == 5,\
                f"Len Data ({len(line)}) needs to be 5!"

            for val in line[:-1]:
                self.fed.write(f"{val} &")
            self.fed.write(f"{line[-1]} \\\\\n")

            #if ind < len(data)-1:
            #    self.fed.write("\\midrule\n")

        self.fed.write("\n")
        self.fed.write("\\bottomrule\n")
        
        self.fed.write(
            "\\end{longtable}\n")
        

    def ranking_table(self, headers, data):

        self.fed.write(
            "\\begin{longtable}[c]{%s}\n"\
            % ("cl" + "c"*(len(headers)-2)))

        self.fed.write("\\toprule\n")

        for header in headers[:-1]:
            self.fed.write(f"{header} &")
        self.fed.write(f"{headers[-1]} \\\\\n")

        self.fed.write("\\midrule\n")
        self.fed.write("\\endhead\n")

        for line in data:
            assert len(line) == len(headers), "Data and Header Info do not match"

            for val in line[:-1]:
                self.fed.write(f"{val} &")
            self.fed.write(f"{line[-1]} \\\\\n")

        self.fed.write("\n")
        self.fed.write("\\bottomrule\n")
        
        self.fed.write(
            "\\end{longtable}\n")

    def race_summary_table(self, class_name, races, data):

        self.fed.write("{\\scriptsize\n")
        self.fed.write(
            "\\begin{longtable}[c]{%s}\n"\
            % ("c" + "lc"*len(races)))

        self.fed.write("\\toprule\n")
        
        self.fed.write("\\multicolumn{%d}{c}{%s} \\\\\n" % (1+2*len(races), class_name))

        self.fed.write("Rank & ")
        
        for race in races[:-1]:
            self.fed.write("\\multicolumn{2}{c}{%s} &" % race)
        self.fed.write("\\multicolumn{2}{c}{%s} \\\\\n" % races[-1])

        self.fed.write(" & ")
        for race in races[:-1]:
            self.fed.write("Athlete & Points & ")
        self.fed.write("Athlete & Points \\\\\n")
        
        self.fed.write("\\midrule\n")
        self.fed.write("\\endhead\n")

        for ind, line in enumerate(data):
            assert len(line) == len(races)*2, "Data and Header Info do not match"

            self.fed.write(f"{ind+1} &")

            for val in line[:-1]:
                self.fed.write(f"{val} &")
            self.fed.write(f"{line[-1]} \\\\\n")

            if ind < len(data)-1:
                self.fed.write("\\midrule\n")
        
        self.fed.write("\n")
        self.fed.write("\\bottomrule\n")
        
        self.fed.write(
            "\\end{longtable}\n")
        self.fed.write("}\n")
        
    def close(self):

        self.fed.write("\n\\end{document}\n")

        self.fed.close()

        # Run twice so the table of contents is filled in
        directory, filename = os.path.split(os.path.abspath(self.filename))
        cmd = ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', filename]
        output = subprocess.DEVNULL if self.quiet else None
        subprocess.check_call(cmd, cwd=directory, stdout=output)
        subprocess.check_call(cmd, cwd=directory, stdout=output)

        self.fed = None

    def __del__(self):

        if self.fed is not None:
            self.close()
