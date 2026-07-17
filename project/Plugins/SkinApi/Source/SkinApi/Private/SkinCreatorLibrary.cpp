#include "SkinCreatorLibrary.h"
#include "KeyEventReceiver.h"

#include "UObject/Package.h"

static UKeyEventReceiver* GStubReceiver = nullptr;

UKeyEventReceiver* USkinCreatorLibrary::GetKeyEventReceiver()
{
    if (GStubReceiver == nullptr)
    {
        GStubReceiver = NewObject<UKeyEventReceiver>(GetTransientPackage());
        if (GStubReceiver)
        {
            GStubReceiver->AddToRoot();
            UE_LOG(LogTemp, Display, TEXT("[CPPRO SkinApi Stub] Created key-event receiver"));
        }
    }
    return GStubReceiver;
}

int32 USkinCreatorLibrary::FKeyToUSBUsageID(FKey Key)
{
    (void)Key;
    return 0;
}

int32 USkinCreatorLibrary::GetKeyIndexByUsageId(int32 UsageId)
{
    return UsageId;
}

FKey USkinCreatorLibrary::KeyIndexToFKey(int32 KeyIndex)
{
    (void)KeyIndex;
    return EKeys::Invalid;
}

FVector2D USkinCreatorLibrary::GetPositionByKeyIndex(int32 KeyIndex)
{
    (void)KeyIndex;
    return FVector2D::ZeroVector;
}

FVector2D USkinCreatorLibrary::GetKeyNormalizedScreenSpace(int32 KeyIndex)
{
    (void)KeyIndex;
    return FVector2D::ZeroVector;
}

FVector2D USkinCreatorLibrary::KeyboardSpaceToNormailzedWorldSpace(FVector2D KeyboardSpace)
{
    return KeyboardSpace;
}

void USkinCreatorLibrary::GetKeyWorldPositionDirectionAtDistance(int32 KeyIndex, float Distance, FVector& OutPosition, FVector& OutDirection)
{
    (void)KeyIndex;
    (void)Distance;
    OutPosition = FVector::ZeroVector;
    OutDirection = FVector(1, 0, 0);
}

void USkinCreatorLibrary::DrawKeyboardFromCamera()
{
}
