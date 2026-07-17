#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "KeyEventReceiver.generated.h"

// Minimal authoring declaration matching the confirmed device callback ABI.
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(
    FSkinKeyEvent,
    uint8, HCode,
    bool, IsActuated,
    int32, Percentage
);

UCLASS(BlueprintType)
class SKINAPI_API UKeyEventReceiver : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable, Category = "SkinApi")
    FSkinKeyEvent OnKeyEvent;

    UFUNCTION(BlueprintCallable, Category = "SkinApi|Stub")
    void EmitTestKeyEvent(uint8 HCode, bool IsActuated, int32 Percentage);
};
