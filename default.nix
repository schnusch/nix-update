{ pkgs ?  import <nixpkgs> {},
  src ? ./.
}:


with pkgs;
python3.pkgs.buildPythonApplication rec {
  name = "nix-update";
  inherit src;
  buildInputs = [ makeWrapper ];
  checkInputs = [
    python3.pkgs.pytest
    python3.pkgs.black
    python3.pkgs.flake8
    python3.pkgs.isort
    glibcLocales
    mypy
    # technically not a test input, but we need it for development in PATH
    pkgs.nixVersions.stable or nix_2_4
  ];
  checkPhase = ''
    echo -e "\x1b[32m## run black\x1b[0m"
    LC_ALL=en_US.utf-8 black --check . bin/nix-update
    echo -e "\x1b[32m## run flake8\x1b[0m"
    flake8 nix_update
    echo -e "\x1b[32m## run mypy\x1b[0m"
    mypy --no-warn-unused-ignores --strict nix_update tests

    echo -e "\x1b[32m## run isort\x1b[0m"
    isort . --check-only
  '';
  makeWrapperArgs = [
    "--prefix PATH" ":" (lib.makeBinPath [ pkgs.nixVersions.stable or nix_2_4 nixpkgs-fmt nixpkgs-review ])
  ];
  shellHook = ''
    # workaround because `python setup.py develop` breaks for me
  '';

  passthru.env = buildEnv { inherit name; paths = buildInputs ++ checkInputs; };
}
