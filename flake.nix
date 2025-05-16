{
  description = "AI Terminal - AI-powered terminal command assistant";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonPackages = pkgs.python310Packages;
        
        aiterm = pythonPackages.buildPythonApplication {
          pname = "aiterm";
          version = "0.1.0";
          
          src = ./.;
          
          propagatedBuildInputs = with pythonPackages; [
            click
            rich
            pyyaml
            requests
            openai
          ];
          
          # Ensure the CLI script is executable
          postInstall = ''
            chmod +x $out/bin/at
          '';
        };
      in
      {
        packages = {
          default = aiterm;
          aiterm = aiterm;
        };
        
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python310
            pythonPackages.pip
            pythonPackages.setuptools
            pythonPackages.wheel
            pythonPackages.virtualenv
          ] ++ aiterm.propagatedBuildInputs;
          
          shellHook = ''
            echo "aiterm development shell"
            echo "Run 'python setup.py install' to install in development mode"
          '';
        };
        
        apps.default = {
          type = "app";
          program = "${aiterm}/bin/at";
        };
      });
}
