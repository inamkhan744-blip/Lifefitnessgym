{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.gcc
    pkgs.libgcc
    pkgs.stdenv.cc.cc.lib
    pkgs.postgresql
  ];
}
