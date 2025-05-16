{
  description = "AITerm - AI-powered terminal command assistant";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    let
      # System-agnostic outputs like NixOS modules
      systemAgnostic = {
        # NixOS module
        nixosModules.default = { config, lib, pkgs, ... }:
          with lib;
          let
            cfg = config.programs.aiterm;
          in {
            options.programs.aiterm = {
              enable = mkEnableOption "AITerm - AI terminal command assistant";
              
              package = mkOption {
                type = types.package;
                default = self.packages.${pkgs.system}.default;
                description = "AITerm package to use";
              };
              
              defaultConfig = mkOption {
                type = types.nullOr types.attrs;
                default = null;
                description = "Default configuration for AITerm";
              };
            };
            
            config = mkIf cfg.enable {
              environment.systemPackages = [ cfg.package ];
              
              # Optionally create default config
              environment.etc = mkIf (cfg.defaultConfig != null) {
                "aiterm/config.yaml".text = builtins.toJSON cfg.defaultConfig;
              };
            };
          };
      };
      
      # System-specific outputs
      systemSpecific = flake-utils.lib.eachDefaultSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          
          pythonPackages = pkgs.python312Packages;
          
          aiterm = pythonPackages.buildPythonApplication rec {
            pname = "aiterm";
            version = "0.1.0";
            
            src = ./.;
            
            # Ensure we use the build system properly
            format = "setuptools";
            
            # Build dependencies
            nativeBuildInputs = with pythonPackages; [
              setuptools
              wheel
            ] ++ (with pkgs; [
              makeWrapper
            ]);
            
            # Runtime dependencies
            propagatedBuildInputs = with pythonPackages; [
              click
              openai
              anthropic
              pyyaml
              requests
              rich
              aiohttp
              mmh3
              bitarray
            ];
            
            # Configure the build
            preBuild = ''
              # Clean up any conflicting files
              rm -f ait src/ait
            '';

            # Ensure proper install and wrapper
            postInstall = ''
              # Wrap the installed script with proper environment
              wrapProgram $out/bin/ait \
                --prefix PYTHONPATH : "$PYTHONPATH"
            '';
            
            # Disable tests during build (run them separately)
            doCheck = false;
            
            meta = with pkgs.lib; {
              description = "AI-powered terminal command assistant";
              homepage = "https://github.com/0kenx/aiterm";
              license = licenses.mit;
              maintainers = with maintainers; [ ];
              platforms = platforms.unix;
            };
          };
        in
        {
          # The default package
          packages = {
            default = aiterm;
            aiterm = aiterm;
          };
          
          # Development shell
          devShells.default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python312
              pythonPackages.pip
              pythonPackages.setuptools
              pythonPackages.wheel
              pythonPackages.virtualenv
              
              # Development tools
              ruff
              black
              mypy
              
              # For uv
              uv
            ] ++ aiterm.propagatedBuildInputs;
            
            shellHook = ''
              echo "AITerm development shell"
              echo "Run 'uv run ait' to test the application"
              echo "Run 'nix build' to build the package"
            '';
          };
          
          # App definition for 'nix run'
          apps.default = {
            type = "app";
            program = "${aiterm}/bin/ait";
          };
          
          # Make it available as an overlay
          overlays.default = final: prev: {
            aiterm = aiterm;
          };
        });
    in
    # Merge system-agnostic and system-specific outputs
    systemAgnostic // systemSpecific;
}