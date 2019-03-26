let
  # Contains the NixOS package collection. ARTIQ depends on some of them, and
  # you may also want certain packages from there.
  pkgs = import <nixpkgs> {};
  # Contains the main ARTIQ packages, their dependencies, and board packages
  # for systems used in CI.
  # List: https://nixbld.m-labs.hk/channel/custom/artiq/main/channel
  m-labs = import <m-labs> { inherit pkgs; };
  # Contains the board packages for the majority of systems.
  # List: https://nixbld.m-labs.hk/channel/custom/artiq/sinara-systems/channel
  sinara = import <sinara> { inherit pkgs; };
in
  pkgs.mkShell {
    buildInputs = [
      (pkgs.python3.withPackages(ps: [
        # List desired Python packages here.
        # The board packages are also "Python" packages. You only need a board
        # package if you intend to reflash that board.
        m-labs.artiq
        m-labs.artiq-board-kc705-nist_clock
        sinara.artiq-board-kasli-wipm
        # from the NixOS package collection:
        ps.paramiko  # needed for flashing boards remotely (artiq_flash -H)
        ps.pandas
        ps.numpy
        ps.scipy
        ps.numba
        ps.matplotlib.override { enableQt = true; }
        ps.bokeh
      ]))
      # List desired non-Python packages here
      m-labs.openocd  # needed for flashing boards locally
      pkgs.spyder
    ];
  }
