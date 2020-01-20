@0xcf6f39416bd85726;

struct MpvCommand {
  # union
  loadFile @0 :LoadFileCommand;
  struct LoadFileCommand {
    path @0 :Text;
  }
}

enum MpvError {
  none @0;
}

interface MpvSockServer {
  execute @0 (userId :Text, cmd :MpvCommand) -> (err :MpvError);
}
