FROM --platform=linux/amd64 sharelatex/sharelatex:6.3.2

COPY init-admin.sh /etc/my_init.d/999_init_admin.sh
RUN chmod +x /etc/my_init.d/999_init_admin.sh

RUN apt-get update && apt-get install -y \
    texlive-lang-portuguese \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-publishers \
    biber \
    && echo "TEXMFLOCAL = /usr/local/texlive/texmf-local:/usr/share/texlive/texmf-dist" \
    >> "$(ls -d /usr/local/texlive/20* | tail -1)/texmf.cnf" \
    && mktexlsr /usr/share/texlive/texmf-dist \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*