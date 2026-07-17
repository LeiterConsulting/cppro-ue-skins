using UnrealBuildTool;
using System.Collections.Generic;

public class sparkTarget : TargetRules
{
    public sparkTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V2;
        ExtraModuleNames.AddRange(new string[] { "spark" });
    }
}
