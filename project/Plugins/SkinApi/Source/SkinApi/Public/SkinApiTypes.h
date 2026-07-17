#pragma once

#include "CoreMinimal.h"
#include "SkinApiTypes.generated.h"

USTRUCT(BlueprintType)
struct SKINAPI_API FSkinApiDummy
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Dummy = 0;
};
