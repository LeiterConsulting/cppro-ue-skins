#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "InputCoreTypes.h"
#include "SkinCreatorLibrary.generated.h"

class UKeyEventReceiver;

UCLASS()
class SKINAPI_API USkinCreatorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "SkinApi")
    static UKeyEventReceiver* GetKeyEventReceiver();

    UFUNCTION(BlueprintPure, Category = "SkinApi")
    static int32 FKeyToUSBUsageID(FKey Key);

    UFUNCTION(BlueprintPure, Category = "SkinApi")
    static int32 GetKeyIndexByUsageId(int32 UsageId);

    UFUNCTION(BlueprintPure, Category = "SkinApi")
    static FKey KeyIndexToFKey(int32 KeyIndex);

    UFUNCTION(BlueprintPure, Category = "SkinApi")
    static FVector2D GetPositionByKeyIndex(int32 KeyIndex);

    UFUNCTION(BlueprintPure, Category = "SkinApi")
    static FVector2D GetKeyNormalizedScreenSpace(int32 KeyIndex);

    UFUNCTION(BlueprintPure, Category = "SkinApi")
    static FVector2D KeyboardSpaceToNormailzedWorldSpace(FVector2D KeyboardSpace);

    UFUNCTION(BlueprintCallable, Category = "SkinApi")
    static void GetKeyWorldPositionDirectionAtDistance(int32 KeyIndex, float Distance, FVector& OutPosition, FVector& OutDirection);

    UFUNCTION(BlueprintCallable, Category = "SkinApi")
    static void DrawKeyboardFromCamera();
};
