#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MoodfieldAuthoringLibrary.generated.h"

/**
 * Small editor-only bridge used by tools/ue-moodfield-build.py.
 *
 * WidgetTree and Blueprint graph internals are not exposed by UE 4.27's
 * experimental Python API.  Keeping the narrowly scoped mutation here makes
 * the authoring build deterministic while the cooked skin remains ordinary
 * Blueprint, UMG, and material content.
 */
UCLASS()
class SPARK_API UMoodfieldAuthoringLibrary
    : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** Compatibility alias for ConfigureMoodfieldRuntimeAssets. */
    UFUNCTION(BlueprintCallable, Category = "CPPRO|Moodfield|Authoring")
    static bool ConfigureMoodfieldAssets();

    UFUNCTION(BlueprintCallable, Category = "CPPRO|Moodfield|Authoring")
    static bool ConfigureMoodfieldRuntimeAssets();
};
