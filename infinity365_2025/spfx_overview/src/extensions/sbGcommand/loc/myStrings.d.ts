declare interface ISbGcommandCommandSetStrings {
  Command1: string;
  Command2: string;
}

declare module 'SbGcommandCommandSetStrings' {
  const strings: ISbGcommandCommandSetStrings;
  export = strings;
}
