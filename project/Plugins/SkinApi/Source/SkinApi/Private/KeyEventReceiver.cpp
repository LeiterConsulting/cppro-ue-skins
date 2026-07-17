#include "KeyEventReceiver.h"

void UKeyEventReceiver::EmitTestKeyEvent(uint8 HCode, bool IsActuated, int32 Percentage)
{
    OnKeyEvent.Broadcast(HCode, IsActuated, Percentage);
}
