using UnrealBuildTool;
using System.Collections.Generic;

public class sparkEditorTarget : TargetRules
{
    public sparkEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V2;
        ExtraModuleNames.AddRange(new string[] { "spark" });
    }
}
