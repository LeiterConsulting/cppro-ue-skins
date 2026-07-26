#include "MoodfieldAuthoringLibrary.h"

#if WITH_EDITOR
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphSchema_K2.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "K2Node_CallFunction.h"
#include "K2Node_ExecutionSequence.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Kismet/KismetMathLibrary.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialInterface.h"
#include "UObject/UnrealType.h"
#include "WidgetBlueprint.h"
#endif

#if WITH_EDITOR
namespace MoodfieldAuthoring
{
    static const FName Marker(TEXT("MOODFIELD_CLASSIFIER_V1"));
    static const FName EventClockMarker(
        TEXT("MOODFIELD_CONTACT_EVENT_V3")
    );
    static const FName TrailMarker(TEXT("MOODFIELD_TRAILS_V3"));
    static const FName MoodMemoryMarker(
        TEXT("MOODFIELD_REGIONAL_MEMORY_V1")
    );
    static const FName LongMoodMarker(
        TEXT("MOODFIELD_LONG_MASS_V1")
    );
    static const FName PatternShareMarker(
        TEXT("MOODFIELD_PATTERN_SHARES_V1")
    );
    static const FName BilateralShareMarker(
        TEXT("MOODFIELD_BILATERAL_ALPHA_V1")
    );
    static const FName ProseZoneMarker(
        TEXT("MOODFIELD_PROSE_ZONES_V1")
    );

    static bool DisableLegacyForegroundEffects(
        UWidgetBlueprint* WidgetBlueprint
    )
    {
        if (!WidgetBlueprint || !WidgetBlueprint->WidgetTree)
        {
            return false;
        }

        // Keyfield Pulse's mapped Borders remain valuable as a proven input
        // routing surface, but their rectangular A2-era light, release-pad,
        // and wave brushes do not belong above Moodfield's continuous
        // substrate.  Runtime Blueprint calls only change visibility, opacity,
        // and scale, so a zero-alpha brush permanently makes these inherited
        // layers optically inert without touching their event graph.
        for (int32 Index = 0; Index < 68; ++Index)
        {
            const FName EffectNames[] = {
                FName(*FString::Printf(
                    TEXT("KeyLight_%02d"),
                    Index
                )),
                FName(*FString::Printf(
                    TEXT("KeyRipple_%02d"),
                    Index
                )),
                FName(*FString::Printf(
                    TEXT("KeyWave_%02d_1"),
                    Index
                )),
                FName(*FString::Printf(
                    TEXT("KeyWave_%02d_2"),
                    Index
                )),
                FName(*FString::Printf(
                    TEXT("KeyWave_%02d_3"),
                    Index
                ))
            };

            for (const FName EffectName : EffectNames)
            {
                UBorder* Effect = WidgetBlueprint->WidgetTree
                    ->FindWidget<UBorder>(EffectName);
                if (!Effect)
                {
                    UE_LOG(
                        LogTemp,
                        Error,
                        TEXT(
                            "Moodfield inherited effect %s was not found."
                        ),
                        *EffectName.ToString()
                    );
                    return false;
                }

                Effect->Modify();
                FLinearColor Color = Effect->BrushColor;
                Color.A = 0.0f;
                Effect->SetBrushColor(Color);
            }
        }

        return true;
    }

    template <typename NodeType>
    NodeType* AddNode(UEdGraph* Graph, int32 X, int32 Y)
    {
        FGraphNodeCreator<NodeType> Creator(*Graph);
        NodeType* Node = Creator.CreateNode();
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    }

    UK2Node_CallFunction* AddCall(
        UEdGraph* Graph,
        UFunction* Function,
        int32 X,
        int32 Y
    )
    {
        if (!Function)
        {
            return nullptr;
        }

        FGraphNodeCreator<UK2Node_CallFunction> Creator(*Graph);
        UK2Node_CallFunction* Node = Creator.CreateNode();
        Node->SetFromFunction(Function);
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    }

    UK2Node_VariableGet* AddGet(
        UEdGraph* Graph,
        FName VariableName,
        int32 X,
        int32 Y
    )
    {
        FGraphNodeCreator<UK2Node_VariableGet> Creator(*Graph);
        UK2Node_VariableGet* Node = Creator.CreateNode();
        Node->VariableReference.SetSelfMember(VariableName);
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    }

    UK2Node_VariableSet* AddSet(
        UEdGraph* Graph,
        FName VariableName,
        int32 X,
        int32 Y
    )
    {
        FGraphNodeCreator<UK2Node_VariableSet> Creator(*Graph);
        UK2Node_VariableSet* Node = Creator.CreateNode();
        Node->VariableReference.SetSelfMember(VariableName);
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    }

    UEdGraphPin* Pin(UEdGraphNode* Node, const TCHAR* Name)
    {
        return Node ? Node->FindPin(FName(Name)) : nullptr;
    }

    bool Link(
        const UEdGraphSchema_K2* Schema,
        UEdGraphPin* Output,
        UEdGraphPin* Input
    )
    {
        return Schema && Output && Input
            && Schema->TryCreateConnection(Output, Input);
    }

    void SetFloatDefault(
        const UEdGraphSchema_K2* Schema,
        UEdGraphPin* PinToSet,
        float Value
    )
    {
        if (Schema && PinToSet)
        {
            Schema->TrySetDefaultValue(
                *PinToSet,
                FString::SanitizeFloat(Value)
            );
        }
    }

    void SetByteDefault(
        const UEdGraphSchema_K2* Schema,
        UEdGraphPin* PinToSet,
        uint8 Value
    )
    {
        if (Schema && PinToSet)
        {
            Schema->TrySetDefaultValue(
                *PinToSet,
                FString::FromInt(static_cast<int32>(Value))
            );
        }
    }

    void EnsureVariable(
        UBlueprint* Blueprint,
        FName Name,
        const FName& Category,
        const TCHAR* DefaultValue
    )
    {
        for (const FBPVariableDescription& Variable :
            Blueprint->NewVariables)
        {
            if (Variable.VarName == Name)
            {
                return;
            }
        }

        FEdGraphPinType Type;
        Type.PinCategory = Category;
        FBlueprintEditorUtils::AddMemberVariable(
            Blueprint,
            Name,
            Type,
            DefaultValue
        );
    }

    UK2Node_CallFunction* AddFloatMath(
        UEdGraph* Graph,
        UFunction* Function,
        UEdGraphPin* A,
        float B,
        int32 X,
        int32 Y
    )
    {
        UK2Node_CallFunction* Node = AddCall(Graph, Function, X, Y);
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        Link(Schema, A, Pin(Node, TEXT("A")));
        SetFloatDefault(Schema, Pin(Node, TEXT("B")), B);
        return Node;
    }

    UK2Node_CallFunction* AddSelectFloat(
        UEdGraph* Graph,
        UEdGraphPin* Condition,
        float TrueValue,
        float FalseValue,
        int32 X,
        int32 Y
    )
    {
        UFunction* Function =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    SelectFloat
                )
            );
        UK2Node_CallFunction* Node = AddCall(Graph, Function, X, Y);
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        SetFloatDefault(Schema, Pin(Node, TEXT("A")), TrueValue);
        SetFloatDefault(Schema, Pin(Node, TEXT("B")), FalseValue);
        Link(Schema, Condition, Pin(Node, TEXT("bPickA")));
        return Node;
    }

    UK2Node_CallFunction* AddMpcSetter(
        UEdGraph* Graph,
        UMaterialParameterCollection* Collection,
        const TCHAR* ParameterName,
        UEdGraphPin* Value,
        int32 X,
        int32 Y
    )
    {
        UFunction* Function =
            UKismetMaterialLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMaterialLibrary,
                    SetScalarParameterValue
                )
            );
        UK2Node_CallFunction* Node = AddCall(Graph, Function, X, Y);
        UEdGraphPin* CollectionPin = Pin(Node, TEXT("Collection"));
        UEdGraphPin* NamePin = Pin(Node, TEXT("ParameterName"));
        if (CollectionPin)
        {
            CollectionPin->DefaultObject = Collection;
        }
        if (NamePin)
        {
            NamePin->DefaultValue = ParameterName;
        }
        Link(
            GetDefault<UEdGraphSchema_K2>(),
            Value,
            Pin(Node, TEXT("ParameterValue"))
        );
        return Node;
    }

    bool AddClassifier(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();

        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    Marker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                int32 SetterCount = 0;
                int32 MarkerCount = 0;
                for (UEdGraphNode* Candidate : Graph->Nodes)
                {
                    if (
                        Candidate
                        && Candidate->NodeComment.Equals(
                            Marker.ToString(),
                            ESearchCase::CaseSensitive
                        )
                    )
                    {
                        ++MarkerCount;
                    }
                    UK2Node_CallFunction* Call =
                        Cast<UK2Node_CallFunction>(Candidate);
                    if (
                        Call
                        && Call->FunctionReference.GetMemberName()
                            == FName(TEXT("SetScalarParameterValue"))
                    )
                    {
                        ++SetterCount;
                        UEdGraphPin* SetterExec = Pin(
                            Call,
                            TEXT("execute")
                        );
                        UEdGraphPin* SetterCollection = Pin(
                            Call,
                            TEXT("Collection")
                        );
                        UEdGraphPin* SetterName = Pin(
                            Call,
                            TEXT("ParameterName")
                        );
                        UEdGraphPin* SetterValue = Pin(
                            Call,
                            TEXT("ParameterValue")
                        );
                        UEdGraphPin* SetterWorld = Pin(
                            Call,
                            TEXT("__WorldContext")
                        );
                        UE_LOG(
                            LogTemp,
                            Display,
                            TEXT(
                                "Moodfield setter %s: exec=%d value=%d "
                                "collection=%s world=%d."
                            ),
                            SetterName
                                ? *SetterName->DefaultValue
                                : TEXT("<missing>"),
                            SetterExec
                                ? SetterExec->LinkedTo.Num()
                                : -1,
                            SetterValue
                                ? SetterValue->LinkedTo.Num()
                                : -1,
                            SetterCollection
                                && SetterCollection->DefaultObject
                                ? *SetterCollection->DefaultObject
                                    ->GetPathName()
                                : TEXT("<missing>"),
                            SetterWorld
                                ? SetterWorld->LinkedTo.Num()
                                : -1
                        );
                    }
                }
                UEdGraphPin* ExecutePin = Pin(Existing, TEXT("execute"));
                UEdGraphPin* ConditionPin = Pin(
                    Existing,
                    TEXT("Condition")
                );
                UE_LOG(
                    LogTemp,
                    Display,
                    TEXT(
                        "Moodfield classifier graph: marker exec=%d, "
                        "condition=%d, markers=%d, MPC setters=%d."
                    ),
                    ExecutePin ? ExecutePin->LinkedTo.Num() : -1,
                    ConditionPin ? ConditionPin->LinkedTo.Num() : -1,
                    MarkerCount,
                    SetterCount
                );
                return true;
            }
        }

        EnsureVariable(
            Blueprint,
            FName(TEXT("MoodfieldGlobal")),
            UEdGraphSchema_K2::PC_Float,
            TEXT("0.18")
        );
        EnsureVariable(
            Blueprint,
            FName(TEXT("MoodfieldTyping")),
            UEdGraphSchema_K2::PC_Float,
            TEXT("0.12")
        );
        EnsureVariable(
            Blueprint,
            FName(TEXT("MoodfieldGame")),
            UEdGraphSchema_K2::PC_Float,
            TEXT("0.0")
        );
        EnsureVariable(
            Blueprint,
            FName(TEXT("MoodfieldLastEvent")),
            UEdGraphSchema_K2::PC_Float,
            TEXT("0.0")
        );
        EnsureVariable(
            Blueprint,
            FName(TEXT("MoodfieldLastKey")),
            UEdGraphSchema_K2::PC_Byte,
            TEXT("255")
        );

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            UE_LOG(
                LogTemp,
                Error,
                TEXT("Moodfield raw key event was not found.")
            );
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            UE_LOG(
                LogTemp,
                Error,
                TEXT("Moodfield root execution sequence was not found.")
            );
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* ClassifierExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                ClassifierExec = Candidate;
                break;
            }
        }
        if (!ClassifierExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 1850;

        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = Marker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, ClassifierExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* GetTimeFunction =
            UKismetSystemLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetSystemLibrary,
                    GetGameTimeInSeconds
                )
            );
        UK2Node_CallFunction* Time =
            AddCall(Graph, GetTimeFunction, X + 260, Y - 420);

        UK2Node_VariableGet* LastEventGet = AddGet(
            Graph,
            FName(TEXT("MoodfieldLastEvent")),
            X + 260,
            Y - 250
        );
        UFunction* SubtractFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Subtract_FloatFloat
                )
            );
        UK2Node_CallFunction* Interval = AddCall(
            Graph,
            SubtractFunction,
            X + 500,
            Y - 340
        );
        Link(Schema, Pin(Time, TEXT("ReturnValue")), Pin(Interval, TEXT("A")));
        Link(
            Schema,
            Pin(LastEventGet, TEXT("MoodfieldLastEvent")),
            Pin(Interval, TEXT("B"))
        );

        UFunction* LessFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Less_FloatFloat
                )
            );
        UK2Node_CallFunction* IsBurst = AddCall(
            Graph,
            LessFunction,
            X + 760,
            Y - 340
        );
        Link(
            Schema,
            Pin(Interval, TEXT("ReturnValue")),
            Pin(IsBurst, TEXT("A"))
        );
        SetFloatDefault(Schema, Pin(IsBurst, TEXT("B")), 0.16f);
        UK2Node_CallFunction* BurstValue = AddSelectFloat(
            Graph,
            Pin(IsBurst, TEXT("ReturnValue")),
            1.0f,
            0.18f,
            X + 1010,
            Y - 340
        );

        UK2Node_VariableGet* LastKeyGet = AddGet(
            Graph,
            FName(TEXT("MoodfieldLastKey")),
            X + 500,
            Y - 120
        );
        UFunction* EqualByteFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    EqualEqual_ByteByte
                )
            );
        UK2Node_CallFunction* IsRepeat = AddCall(
            Graph,
            EqualByteFunction,
            X + 760,
            Y - 120
        );
        Link(Schema, HCodePin, Pin(IsRepeat, TEXT("A")));
        Link(
            Schema,
            Pin(LastKeyGet, TEXT("MoodfieldLastKey")),
            Pin(IsRepeat, TEXT("B"))
        );
        UK2Node_CallFunction* RepeatValue = AddSelectFloat(
            Graph,
            Pin(IsRepeat, TEXT("ReturnValue")),
            1.0f,
            0.0f,
            X + 1010,
            Y - 120
        );

        const uint8 GameKeys[] = {
            18, 33, 34, 35, 45, 56, 58, 61, 64
        };
        TArray<UEdGraphPin*> GameConditions;
        int32 GameY = Y + 180;
        for (uint8 GameKey : GameKeys)
        {
            UK2Node_CallFunction* Equal = AddCall(
                Graph,
                EqualByteFunction,
                X + 260,
                GameY
            );
            Link(Schema, HCodePin, Pin(Equal, TEXT("A")));
            SetByteDefault(Schema, Pin(Equal, TEXT("B")), GameKey);
            GameConditions.Add(Pin(Equal, TEXT("ReturnValue")));
            GameY += 120;
        }

        UFunction* OrFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    BooleanOR
                )
            );
        UEdGraphPin* IsGamePin = GameConditions[0];
        int32 OrY = Y + 180;
        for (int32 Index = 1; Index < GameConditions.Num(); ++Index)
        {
            UK2Node_CallFunction* OrNode = AddCall(
                Graph,
                OrFunction,
                X + 520 + Index * 180,
                OrY
            );
            Link(Schema, IsGamePin, Pin(OrNode, TEXT("A")));
            Link(
                Schema,
                GameConditions[Index],
                Pin(OrNode, TEXT("B"))
            );
            IsGamePin = Pin(OrNode, TEXT("ReturnValue"));
            OrY += 60;
        }

        UK2Node_CallFunction* GameImpulse = AddSelectFloat(
            Graph,
            IsGamePin,
            0.24f,
            0.0f,
            X + 2060,
            Y + 330
        );
        UK2Node_CallFunction* TypingImpulse = AddSelectFloat(
            Graph,
            IsGamePin,
            0.0f,
            0.07f,
            X + 2060,
            Y + 500
        );

        UFunction* MultiplyFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Multiply_FloatFloat
                )
            );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UFunction* ClampFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    FClamp
                )
            );

        auto BuildScore = [&](
            const TCHAR* VariableName,
            float Retention,
            UEdGraphPin* Impulse,
            int32 ScoreY
        ) -> UEdGraphPin*
        {
            UK2Node_VariableGet* Get = AddGet(
                Graph,
                FName(VariableName),
                X + 2050,
                ScoreY
            );
            UK2Node_CallFunction* Multiply = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(Get, VariableName),
                Retention,
                X + 2290,
                ScoreY
            );
            UK2Node_CallFunction* Add = AddCall(
                Graph,
                AddFunction,
                X + 2530,
                ScoreY
            );
            Link(
                Schema,
                Pin(Multiply, TEXT("ReturnValue")),
                Pin(Add, TEXT("A"))
            );
            Link(Schema, Impulse, Pin(Add, TEXT("B")));
            UK2Node_CallFunction* Clamp = AddCall(
                Graph,
                ClampFunction,
                X + 2770,
                ScoreY
            );
            Link(
                Schema,
                Pin(Add, TEXT("ReturnValue")),
                Pin(Clamp, TEXT("Value"))
            );
            SetFloatDefault(Schema, Pin(Clamp, TEXT("Min")), 0.0f);
            SetFloatDefault(Schema, Pin(Clamp, TEXT("Max")), 1.0f);
            return Pin(Clamp, TEXT("ReturnValue"));
        };

        UEdGraphPin* NewGame = BuildScore(
            TEXT("MoodfieldGame"),
            0.92f,
            Pin(GameImpulse, TEXT("ReturnValue")),
            Y + 820
        );
        UEdGraphPin* NewTyping = BuildScore(
            TEXT("MoodfieldTyping"),
            0.96f,
            Pin(TypingImpulse, TEXT("ReturnValue")),
            Y + 1040
        );

        UK2Node_VariableGet* GlobalGet = AddGet(
            Graph,
            FName(TEXT("MoodfieldGlobal")),
            X + 2050,
            Y + 1260
        );
        UK2Node_CallFunction* GlobalMultiply = AddFloatMath(
            Graph,
            MultiplyFunction,
            Pin(GlobalGet, TEXT("MoodfieldGlobal")),
            0.88f,
            X + 2290,
            Y + 1260
        );
        UK2Node_CallFunction* GlobalAdd = AddCall(
            Graph,
            AddFunction,
            X + 2530,
            Y + 1260
        );
        Link(
            Schema,
            Pin(GlobalMultiply, TEXT("ReturnValue")),
            Pin(GlobalAdd, TEXT("A"))
        );
        SetFloatDefault(Schema, Pin(GlobalAdd, TEXT("B")), 0.22f);
        UK2Node_CallFunction* GlobalClamp = AddCall(
            Graph,
            ClampFunction,
            X + 2770,
            Y + 1260
        );
        Link(
            Schema,
            Pin(GlobalAdd, TEXT("ReturnValue")),
            Pin(GlobalClamp, TEXT("Value"))
        );
        SetFloatDefault(Schema, Pin(GlobalClamp, TEXT("Min")), 0.0f);
        SetFloatDefault(Schema, Pin(GlobalClamp, TEXT("Max")), 1.0f);
        UEdGraphPin* NewGlobal = Pin(GlobalClamp, TEXT("ReturnValue"));

        UFunction* ByteToFloatFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Conv_ByteToFloat
                )
            );
        UK2Node_CallFunction* KeyAsFloat = AddCall(
            Graph,
            ByteToFloatFunction,
            X + 1240,
            Y + 20
        );
        Link(Schema, HCodePin, Pin(KeyAsFloat, TEXT("InByte")));

        UK2Node_VariableGet* CapsGet = AddGet(
            Graph,
            FName(TEXT("CapsToggleState")),
            X + 1240,
            Y + 150
        );
        UFunction* BoolToFloatFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Conv_BoolToFloat
                )
            );
        UK2Node_CallFunction* CapsAsFloat = AddCall(
            Graph,
            BoolToFloatFunction,
            X + 1480,
            Y + 150
        );
        Link(
            Schema,
            Pin(CapsGet, TEXT("CapsToggleState")),
            Pin(CapsAsFloat, TEXT("InBool"))
        );

        UK2Node_VariableSet* SetGlobal = AddSet(
            Graph,
            FName(TEXT("MoodfieldGlobal")),
            X + 3200,
            Y
        );
        UK2Node_VariableSet* SetTyping = AddSet(
            Graph,
            FName(TEXT("MoodfieldTyping")),
            X + 3460,
            Y
        );
        UK2Node_VariableSet* SetGame = AddSet(
            Graph,
            FName(TEXT("MoodfieldGame")),
            X + 3720,
            Y
        );
        UK2Node_VariableSet* SetLastEvent = AddSet(
            Graph,
            FName(TEXT("MoodfieldLastEvent")),
            X + 3980,
            Y
        );
        UK2Node_VariableSet* SetLastKey = AddSet(
            Graph,
            FName(TEXT("MoodfieldLastKey")),
            X + 4240,
            Y
        );

        Link(
            Schema,
            Pin(PressedBranch, TEXT("then")),
            Pin(SetGlobal, TEXT("execute"))
        );
        Link(Schema, NewGlobal, Pin(SetGlobal, TEXT("MoodfieldGlobal")));
        Link(
            Schema,
            Pin(SetGlobal, TEXT("then")),
            Pin(SetTyping, TEXT("execute"))
        );
        Link(Schema, NewTyping, Pin(SetTyping, TEXT("MoodfieldTyping")));
        Link(
            Schema,
            Pin(SetTyping, TEXT("then")),
            Pin(SetGame, TEXT("execute"))
        );
        Link(Schema, NewGame, Pin(SetGame, TEXT("MoodfieldGame")));
        Link(
            Schema,
            Pin(SetGame, TEXT("then")),
            Pin(SetLastEvent, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(Time, TEXT("ReturnValue")),
            Pin(SetLastEvent, TEXT("MoodfieldLastEvent"))
        );
        Link(
            Schema,
            Pin(SetLastEvent, TEXT("then")),
            Pin(SetLastKey, TEXT("execute"))
        );
        Link(Schema, HCodePin, Pin(SetLastKey, TEXT("MoodfieldLastKey")));

        struct FSetterSpec
        {
            const TCHAR* Name;
            UEdGraphPin* Value;
        };
        const FSetterSpec SetterSpecs[] = {
            {TEXT("MoodGlobal"), NewGlobal},
            {TEXT("MoodTyping"), NewTyping},
            {TEXT("MoodGame"), NewGame},
            {TEXT("MoodBurst"), Pin(BurstValue, TEXT("ReturnValue"))},
            {TEXT("MoodRepeat"), Pin(RepeatValue, TEXT("ReturnValue"))},
            {TEXT("MoodCaps"), Pin(CapsAsFloat, TEXT("ReturnValue"))},
            {TEXT("MoodLastEvent"), Pin(Time, TEXT("ReturnValue"))},
            {TEXT("MoodKeyCode"), Pin(KeyAsFloat, TEXT("ReturnValue"))},
            {TEXT("MoodInterval"), Pin(Interval, TEXT("ReturnValue"))}
        };

        UEdGraphPin* ExecOut = Pin(SetLastKey, TEXT("then"));
        int32 SetterX = X + 4520;
        int32 SetterY = Y;
        for (const FSetterSpec& Spec : SetterSpecs)
        {
            UK2Node_CallFunction* Setter = AddMpcSetter(
                Graph,
                Collection,
                Spec.Name,
                Spec.Value,
                SetterX,
                SetterY
            );
            Link(Schema, ExecOut, Pin(Setter, TEXT("execute")));
            ExecOut = Pin(Setter, TEXT("then"));
            SetterX += 260;
            SetterY += 40;
        }

        return true;
    }

    bool AddEventClockBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    EventClockMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* ClockExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                ClockExec = Candidate;
                break;
            }
        }
        if (!ClockExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 2500;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = EventClockMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, ClockExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* AccurateTimeFunction =
            UGameplayStatics::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UGameplayStatics,
                    GetAccurateRealTime
                )
            );
        UK2Node_CallFunction* AccurateTime = AddCall(
            Graph,
            AccurateTimeFunction,
            X + 260,
            Y - 100
        );

        UFunction* IntToFloatFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Conv_IntToFloat
                )
            );
        UK2Node_CallFunction* SecondsAsFloat = AddCall(
            Graph,
            IntToFloatFunction,
            X + 520,
            Y - 160
        );
        Link(
            Schema,
            Pin(AccurateTime, TEXT("Seconds")),
            Pin(SecondsAsFloat, TEXT("InInt"))
        );

        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UK2Node_CallFunction* CombinedTime = AddCall(
            Graph,
            AddFunction,
            X + 760,
            Y - 100
        );
        Link(
            Schema,
            Pin(SecondsAsFloat, TEXT("ReturnValue")),
            Pin(CombinedTime, TEXT("A"))
        );
        Link(
            Schema,
            Pin(AccurateTime, TEXT("PartialSeconds")),
            Pin(CombinedTime, TEXT("B"))
        );

        UFunction* ByteToFloatFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Conv_ByteToFloat
                )
            );
        UK2Node_CallFunction* KeyAsFloat = AddCall(
            Graph,
            ByteToFloatFunction,
            X + 780,
            Y + 150
        );
        Link(Schema, HCodePin, Pin(KeyAsFloat, TEXT("InByte")));

        UK2Node_CallFunction* ContactSetter = AddMpcSetter(
            Graph,
            Collection,
            TEXT("MoodContactCode"),
            Pin(KeyAsFloat, TEXT("ReturnValue")),
            X + 1040,
            Y
        );
        UK2Node_CallFunction* ClockSetter = AddMpcSetter(
            Graph,
            Collection,
            TEXT("MoodEventClock"),
            Pin(CombinedTime, TEXT("ReturnValue")),
            X + 1300,
            Y
        );
        Link(
            Schema,
            Pin(PressedBranch, TEXT("then")),
            Pin(ContactSetter, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(ContactSetter, TEXT("then")),
            Pin(ClockSetter, TEXT("execute"))
        );
        return true;
    }

    bool AddTrailBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    TrailMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        const TCHAR* TrailVariables[] = {
            TEXT("MoodTrail0Code"),
            TEXT("MoodTrail0Clock"),
            TEXT("MoodTrail1Code"),
            TEXT("MoodTrail1Clock"),
            TEXT("MoodTrail2Code"),
            TEXT("MoodTrail2Clock")
        };
        for (const TCHAR* Variable : TrailVariables)
        {
            EnsureVariable(
                Blueprint,
                FName(Variable),
                UEdGraphSchema_K2::PC_Float,
                FString(Variable).EndsWith(TEXT("Code"))
                    ? TEXT("-1.0")
                    : TEXT("0.0")
            );
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* TrailExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                TrailExec = Candidate;
                break;
            }
        }
        if (!TrailExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 3150;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = TrailMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, TrailExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UK2Node_VariableGet* OldTrail0Code = AddGet(
            Graph,
            FName(TEXT("MoodTrail0Code")),
            X + 250,
            Y + 160
        );
        UK2Node_VariableGet* OldTrail0Clock = AddGet(
            Graph,
            FName(TEXT("MoodTrail0Clock")),
            X + 250,
            Y + 280
        );
        UK2Node_VariableGet* OldTrail1Code = AddGet(
            Graph,
            FName(TEXT("MoodTrail1Code")),
            X + 250,
            Y + 400
        );
        UK2Node_VariableGet* OldTrail1Clock = AddGet(
            Graph,
            FName(TEXT("MoodTrail1Clock")),
            X + 250,
            Y + 520
        );

        UFunction* ByteToFloatFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Conv_ByteToFloat
                )
            );
        UK2Node_CallFunction* KeyAsFloat = AddCall(
            Graph,
            ByteToFloatFunction,
            X + 250,
            Y - 180
        );
        Link(Schema, HCodePin, Pin(KeyAsFloat, TEXT("InByte")));

        UFunction* AccurateTimeFunction =
            UGameplayStatics::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UGameplayStatics,
                    GetAccurateRealTime
                )
            );
        UK2Node_CallFunction* AccurateTime = AddCall(
            Graph,
            AccurateTimeFunction,
            X + 250,
            Y - 60
        );
        UFunction* IntToFloatFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Conv_IntToFloat
                )
            );
        UK2Node_CallFunction* SecondsAsFloat = AddCall(
            Graph,
            IntToFloatFunction,
            X + 500,
            Y - 100
        );
        Link(
            Schema,
            Pin(AccurateTime, TEXT("Seconds")),
            Pin(SecondsAsFloat, TEXT("InInt"))
        );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UK2Node_CallFunction* CombinedTime = AddCall(
            Graph,
            AddFunction,
            X + 740,
            Y - 60
        );
        Link(
            Schema,
            Pin(SecondsAsFloat, TEXT("ReturnValue")),
            Pin(CombinedTime, TEXT("A"))
        );
        Link(
            Schema,
            Pin(AccurateTime, TEXT("PartialSeconds")),
            Pin(CombinedTime, TEXT("B"))
        );

        UK2Node_VariableSet* SetTrail2Code = AddSet(
            Graph,
            FName(TEXT("MoodTrail2Code")),
            X + 1020,
            Y
        );
        UK2Node_VariableSet* SetTrail2Clock = AddSet(
            Graph,
            FName(TEXT("MoodTrail2Clock")),
            X + 1260,
            Y
        );
        UK2Node_VariableSet* SetTrail1Code = AddSet(
            Graph,
            FName(TEXT("MoodTrail1Code")),
            X + 1500,
            Y
        );
        UK2Node_VariableSet* SetTrail1Clock = AddSet(
            Graph,
            FName(TEXT("MoodTrail1Clock")),
            X + 1740,
            Y
        );
        UK2Node_VariableSet* SetTrail0Code = AddSet(
            Graph,
            FName(TEXT("MoodTrail0Code")),
            X + 1980,
            Y
        );
        UK2Node_VariableSet* SetTrail0Clock = AddSet(
            Graph,
            FName(TEXT("MoodTrail0Clock")),
            X + 2220,
            Y
        );

        Link(
            Schema,
            Pin(PressedBranch, TEXT("then")),
            Pin(SetTrail2Code, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(OldTrail1Code, TEXT("MoodTrail1Code")),
            Pin(SetTrail2Code, TEXT("MoodTrail2Code"))
        );
        Link(
            Schema,
            Pin(SetTrail2Code, TEXT("then")),
            Pin(SetTrail2Clock, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(OldTrail1Clock, TEXT("MoodTrail1Clock")),
            Pin(SetTrail2Clock, TEXT("MoodTrail2Clock"))
        );
        Link(
            Schema,
            Pin(SetTrail2Clock, TEXT("then")),
            Pin(SetTrail1Code, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(OldTrail0Code, TEXT("MoodTrail0Code")),
            Pin(SetTrail1Code, TEXT("MoodTrail1Code"))
        );
        Link(
            Schema,
            Pin(SetTrail1Code, TEXT("then")),
            Pin(SetTrail1Clock, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(OldTrail0Clock, TEXT("MoodTrail0Clock")),
            Pin(SetTrail1Clock, TEXT("MoodTrail1Clock"))
        );
        Link(
            Schema,
            Pin(SetTrail1Clock, TEXT("then")),
            Pin(SetTrail0Code, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(KeyAsFloat, TEXT("ReturnValue")),
            Pin(SetTrail0Code, TEXT("MoodTrail0Code"))
        );
        Link(
            Schema,
            Pin(SetTrail0Code, TEXT("then")),
            Pin(SetTrail0Clock, TEXT("execute"))
        );
        Link(
            Schema,
            Pin(CombinedTime, TEXT("ReturnValue")),
            Pin(SetTrail0Clock, TEXT("MoodTrail0Clock"))
        );

        struct FTrailSetter
        {
            const TCHAR* Name;
            UEdGraphPin* Value;
        };
        UK2Node_VariableGet* NewTrail0Code = AddGet(
            Graph,
            FName(TEXT("MoodTrail0Code")),
            X + 2460,
            Y + 180
        );
        UK2Node_VariableGet* NewTrail0Clock = AddGet(
            Graph,
            FName(TEXT("MoodTrail0Clock")),
            X + 2460,
            Y + 300
        );
        UK2Node_VariableGet* NewTrail1Code = AddGet(
            Graph,
            FName(TEXT("MoodTrail1Code")),
            X + 2460,
            Y + 420
        );
        UK2Node_VariableGet* NewTrail1Clock = AddGet(
            Graph,
            FName(TEXT("MoodTrail1Clock")),
            X + 2460,
            Y + 540
        );
        UK2Node_VariableGet* NewTrail2Code = AddGet(
            Graph,
            FName(TEXT("MoodTrail2Code")),
            X + 2460,
            Y + 660
        );
        UK2Node_VariableGet* NewTrail2Clock = AddGet(
            Graph,
            FName(TEXT("MoodTrail2Clock")),
            X + 2460,
            Y + 780
        );
        const FTrailSetter Setters[] = {
            {
                TEXT("MoodTrail0Code"),
                Pin(NewTrail0Code, TEXT("MoodTrail0Code"))
            },
            {
                TEXT("MoodTrail0Clock"),
                Pin(NewTrail0Clock, TEXT("MoodTrail0Clock"))
            },
            {
                TEXT("MoodTrail1Code"),
                Pin(NewTrail1Code, TEXT("MoodTrail1Code"))
            },
            {
                TEXT("MoodTrail1Clock"),
                Pin(NewTrail1Clock, TEXT("MoodTrail1Clock"))
            },
            {
                TEXT("MoodTrail2Code"),
                Pin(NewTrail2Code, TEXT("MoodTrail2Code"))
            },
            {
                TEXT("MoodTrail2Clock"),
                Pin(NewTrail2Clock, TEXT("MoodTrail2Clock"))
            }
        };

        UEdGraphPin* ExecOut = Pin(SetTrail0Clock, TEXT("then"));
        int32 SetterX = X + 2500;
        for (const FTrailSetter& SetterSpec : Setters)
        {
            UK2Node_CallFunction* Setter = AddMpcSetter(
                Graph,
                Collection,
                SetterSpec.Name,
                SetterSpec.Value,
                SetterX,
                Y
            );
            Link(Schema, ExecOut, Pin(Setter, TEXT("execute")));
            ExecOut = Pin(Setter, TEXT("then"));
            SetterX += 250;
        }
        return true;
    }

    bool AddMoodMemoryBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    MoodMemoryMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        const FName MemoryVariables[] = {
            FName(TEXT("MoodfieldLeftMemory")),
            FName(TEXT("MoodfieldCenterMemory")),
            FName(TEXT("MoodfieldRightMemory"))
        };
        for (const FName Variable : MemoryVariables)
        {
            EnsureVariable(
                Blueprint,
                Variable,
                UEdGraphSchema_K2::PC_Float,
                TEXT("0.08")
            );
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* MemoryExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                MemoryExec = Candidate;
                break;
            }
        }
        if (!MemoryExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 3900;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = MoodMemoryMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, MemoryExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* EqualByteFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    EqualEqual_ByteByte
                )
            );
        UFunction* OrFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    BooleanOR
                )
            );
        UFunction* MultiplyFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Multiply_FloatFloat
                )
            );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UFunction* ClampFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    FClamp
                )
            );
        if (
            !EqualByteFunction
            || !OrFunction
            || !MultiplyFunction
            || !AddFunction
            || !ClampFunction
        )
        {
            return false;
        }

        auto BuildZoneCondition = [&](
            const uint8* Keys,
            int32 KeyCount,
            int32 ZoneY
        ) -> UEdGraphPin*
        {
            UEdGraphPin* Result = nullptr;
            for (int32 Index = 0; Index < KeyCount; ++Index)
            {
                UK2Node_CallFunction* Equal = AddCall(
                    Graph,
                    EqualByteFunction,
                    X + 260 + (Index % 8) * 200,
                    ZoneY + (Index / 8) * 105
                );
                Link(Schema, HCodePin, Pin(Equal, TEXT("A")));
                SetByteDefault(Schema, Pin(Equal, TEXT("B")), Keys[Index]);
                UEdGraphPin* EqualResult = Pin(Equal, TEXT("ReturnValue"));
                if (!Result)
                {
                    Result = EqualResult;
                    continue;
                }

                UK2Node_CallFunction* Or = AddCall(
                    Graph,
                    OrFunction,
                    X + 1960 + Index * 42,
                    ZoneY + Index * 34
                );
                Link(Schema, Result, Pin(Or, TEXT("A")));
                Link(Schema, EqualResult, Pin(Or, TEXT("B")));
                Result = Pin(Or, TEXT("ReturnValue"));
            }
            return Result;
        };

        const uint8 LeftKeys[] = {
            0, 1, 2, 3, 4, 5,
            16, 17, 18, 19, 20, 21,
            32, 33, 34, 35, 36, 37,
            45, 46, 47, 48, 49,
            58, 59, 60
        };
        const uint8 CenterKeys[] = {
            6, 7, 8, 9, 10, 11, 12,
            22, 23, 24, 25, 26, 27,
            38, 39, 40, 41, 42, 43,
            50, 51, 52, 53, 54, 55,
            61, 62, 63
        };
        const uint8 RightKeys[] = {
            13, 14, 15,
            28, 29, 30, 31,
            44, 56, 57,
            64, 65, 66, 67
        };
        UEdGraphPin* ZoneConditions[] = {
            BuildZoneCondition(
                LeftKeys,
                UE_ARRAY_COUNT(LeftKeys),
                Y - 1100
            ),
            BuildZoneCondition(
                CenterKeys,
                UE_ARRAY_COUNT(CenterKeys),
                Y + 100
            ),
            BuildZoneCondition(
                RightKeys,
                UE_ARRAY_COUNT(RightKeys),
                Y + 1300
            )
        };
        if (!ZoneConditions[0] || !ZoneConditions[1] || !ZoneConditions[2])
        {
            return false;
        }

        UEdGraphPin* NewMemoryValues[3] = {};
        for (int32 Zone = 0; Zone < 3; ++Zone)
        {
            const int32 ValueY = Y + Zone * 480;
            UK2Node_VariableGet* OldValue = AddGet(
                Graph,
                MemoryVariables[Zone],
                X + 3400,
                ValueY
            );
            UK2Node_CallFunction* Retained = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(OldValue, *MemoryVariables[Zone].ToString()),
                0.987f,
                X + 3640,
                ValueY
            );
            UK2Node_CallFunction* Impulse = AddSelectFloat(
                Graph,
                ZoneConditions[Zone],
                0.020f,
                0.0f,
                X + 3640,
                ValueY + 140
            );
            UK2Node_CallFunction* Added = AddCall(
                Graph,
                AddFunction,
                X + 3880,
                ValueY
            );
            Link(
                Schema,
                Pin(Retained, TEXT("ReturnValue")),
                Pin(Added, TEXT("A"))
            );
            Link(
                Schema,
                Pin(Impulse, TEXT("ReturnValue")),
                Pin(Added, TEXT("B"))
            );
            UK2Node_CallFunction* Clamped = AddCall(
                Graph,
                ClampFunction,
                X + 4120,
                ValueY
            );
            Link(
                Schema,
                Pin(Added, TEXT("ReturnValue")),
                Pin(Clamped, TEXT("Value"))
            );
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Min")), 0.0f);
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Max")), 1.0f);
            NewMemoryValues[Zone] = Pin(Clamped, TEXT("ReturnValue"));
        }

        const TCHAR* MpcNames[] = {
            TEXT("MoodLeft"),
            TEXT("MoodCenter"),
            TEXT("MoodRight")
        };
        UEdGraphPin* ExecOut = Pin(PressedBranch, TEXT("then"));
        for (int32 Zone = 0; Zone < 3; ++Zone)
        {
            UK2Node_VariableSet* SetMemory = AddSet(
                Graph,
                MemoryVariables[Zone],
                X + 4420 + Zone * 520,
                Y
            );
            Link(Schema, ExecOut, Pin(SetMemory, TEXT("execute")));
            Link(
                Schema,
                NewMemoryValues[Zone],
                Pin(SetMemory, *MemoryVariables[Zone].ToString())
            );

            UK2Node_CallFunction* SetMpc = AddMpcSetter(
                Graph,
                Collection,
                MpcNames[Zone],
                NewMemoryValues[Zone],
                X + 4660 + Zone * 520,
                Y
            );
            Link(
                Schema,
                Pin(SetMemory, TEXT("then")),
                Pin(SetMpc, TEXT("execute"))
            );
            ExecOut = Pin(SetMpc, TEXT("then"));
        }

        return true;
    }

    bool AddLongMoodBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    LongMoodMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        const FName LongVariables[] = {
            FName(TEXT("MoodfieldMassLeft")),
            FName(TEXT("MoodfieldMassCenter")),
            FName(TEXT("MoodfieldMassRight")),
            FName(TEXT("MoodfieldWasdShare")),
            FName(TEXT("MoodfieldActivityMass"))
        };
        const TCHAR* LongDefaults[] = {
            TEXT("0.08"),
            TEXT("0.08"),
            TEXT("0.08"),
            TEXT("0.0"),
            TEXT("0.12")
        };
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(LongVariables); ++Index)
        {
            EnsureVariable(
                Blueprint,
                LongVariables[Index],
                UEdGraphSchema_K2::PC_Float,
                LongDefaults[Index]
            );
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* LongMoodExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                LongMoodExec = Candidate;
                break;
            }
        }
        if (!LongMoodExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 5700;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = LongMoodMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, LongMoodExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* EqualByteFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    EqualEqual_ByteByte
                )
            );
        UFunction* OrFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    BooleanOR
                )
            );
        UFunction* MultiplyFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Multiply_FloatFloat
                )
            );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UFunction* ClampFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    FClamp
                )
            );
        if (
            !EqualByteFunction
            || !OrFunction
            || !MultiplyFunction
            || !AddFunction
            || !ClampFunction
        )
        {
            return false;
        }

        const uint8 WasdKeys[] = { 18, 33, 34, 35 };
        UEdGraphPin* IsWasd = nullptr;
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(WasdKeys); ++Index)
        {
            UK2Node_CallFunction* Equal = AddCall(
                Graph,
                EqualByteFunction,
                X + 260 + Index * 220,
                Y - 500
            );
            Link(Schema, HCodePin, Pin(Equal, TEXT("A")));
            SetByteDefault(
                Schema,
                Pin(Equal, TEXT("B")),
                WasdKeys[Index]
            );
            UEdGraphPin* EqualResult = Pin(Equal, TEXT("ReturnValue"));
            if (!IsWasd)
            {
                IsWasd = EqualResult;
                continue;
            }

            UK2Node_CallFunction* Or = AddCall(
                Graph,
                OrFunction,
                X + 1220 + Index * 220,
                Y - 500
            );
            Link(Schema, IsWasd, Pin(Or, TEXT("A")));
            Link(Schema, EqualResult, Pin(Or, TEXT("B")));
            IsWasd = Pin(Or, TEXT("ReturnValue"));
        }
        if (!IsWasd)
        {
            return false;
        }

        auto BuildLowPass = [&](
            const FName TargetVariable,
            UEdGraphPin* Source,
            float Retention,
            float SourceGain,
            int32 ValueY
        ) -> UEdGraphPin*
        {
            UK2Node_VariableGet* Old = AddGet(
                Graph,
                TargetVariable,
                X + 2200,
                ValueY
            );
            UK2Node_CallFunction* Retained = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(Old, *TargetVariable.ToString()),
                Retention,
                X + 2440,
                ValueY
            );
            UK2Node_CallFunction* WeightedSource = AddFloatMath(
                Graph,
                MultiplyFunction,
                Source,
                SourceGain,
                X + 2440,
                ValueY + 130
            );
            UK2Node_CallFunction* Added = AddCall(
                Graph,
                AddFunction,
                X + 2680,
                ValueY
            );
            Link(
                Schema,
                Pin(Retained, TEXT("ReturnValue")),
                Pin(Added, TEXT("A"))
            );
            Link(
                Schema,
                Pin(WeightedSource, TEXT("ReturnValue")),
                Pin(Added, TEXT("B"))
            );
            UK2Node_CallFunction* Clamped = AddCall(
                Graph,
                ClampFunction,
                X + 2920,
                ValueY
            );
            Link(
                Schema,
                Pin(Added, TEXT("ReturnValue")),
                Pin(Clamped, TEXT("Value"))
            );
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Min")), 0.0f);
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Max")), 1.0f);
            return Pin(Clamped, TEXT("ReturnValue"));
        };

        UEdGraphPin* NewValues[5] = {};
        const FName RegionalVariables[] = {
            FName(TEXT("MoodfieldLeftMemory")),
            FName(TEXT("MoodfieldCenterMemory")),
            FName(TEXT("MoodfieldRightMemory"))
        };
        for (int32 Zone = 0; Zone < 3; ++Zone)
        {
            UK2Node_VariableGet* Regional = AddGet(
                Graph,
                RegionalVariables[Zone],
                X + 1960,
                Y + Zone * 420
            );
            NewValues[Zone] = BuildLowPass(
                LongVariables[Zone],
                Pin(Regional, *RegionalVariables[Zone].ToString()),
                0.992f,
                0.008f,
                Y + Zone * 420
            );
        }

        UK2Node_CallFunction* WasdImpulse = AddSelectFloat(
            Graph,
            IsWasd,
            1.0f,
            0.0f,
            X + 1960,
            Y + 1260
        );
        NewValues[3] = BuildLowPass(
            LongVariables[3],
            Pin(WasdImpulse, TEXT("ReturnValue")),
            0.982f,
            0.018f,
            Y + 1260
        );

        UK2Node_CallFunction* ActivitySource = AddSelectFloat(
            Graph,
            ActuatedPin,
            1.0f,
            0.0f,
            X + 1960,
            Y + 1680
        );
        NewValues[4] = BuildLowPass(
            LongVariables[4],
            Pin(ActivitySource, TEXT("ReturnValue")),
            0.995f,
            0.006f,
            Y + 1680
        );

        const TCHAR* MpcNames[] = {
            TEXT("MoodMassLeft"),
            TEXT("MoodMassCenter"),
            TEXT("MoodMassRight"),
            TEXT("MoodWasdShare"),
            TEXT("MoodActivityMass")
        };
        UEdGraphPin* ExecOut = Pin(PressedBranch, TEXT("then"));
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(LongVariables); ++Index)
        {
            UK2Node_VariableSet* SetValue = AddSet(
                Graph,
                LongVariables[Index],
                X + 3300 + Index * 510,
                Y
            );
            Link(Schema, ExecOut, Pin(SetValue, TEXT("execute")));
            Link(
                Schema,
                NewValues[Index],
                Pin(SetValue, *LongVariables[Index].ToString())
            );

            UK2Node_CallFunction* SetMpc = AddMpcSetter(
                Graph,
                Collection,
                MpcNames[Index],
                NewValues[Index],
                X + 3540 + Index * 510,
                Y
            );
            Link(
                Schema,
                Pin(SetValue, TEXT("then")),
                Pin(SetMpc, TEXT("execute"))
            );
            ExecOut = Pin(SetMpc, TEXT("then"));
        }

        return true;
    }

    bool AddPatternShareBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    PatternShareMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        const FName ShareVariables[] = {
            FName(TEXT("MoodfieldAlphaShare")),
            FName(TEXT("MoodfieldNavShare"))
        };
        for (const FName Variable : ShareVariables)
        {
            EnsureVariable(
                Blueprint,
                Variable,
                UEdGraphSchema_K2::PC_Float,
                TEXT("0.0")
            );
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* PatternExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                PatternExec = Candidate;
                break;
            }
        }
        if (!PatternExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 7900;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = PatternShareMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, PatternExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* EqualByteFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    EqualEqual_ByteByte
                )
            );
        UFunction* OrFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    BooleanOR
                )
            );
        UFunction* MultiplyFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Multiply_FloatFloat
                )
            );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UFunction* ClampFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    FClamp
                )
            );
        if (
            !EqualByteFunction
            || !OrFunction
            || !MultiplyFunction
            || !AddFunction
            || !ClampFunction
        )
        {
            return false;
        }

        auto BuildSetCondition = [&](
            const uint8* Keys,
            int32 KeyCount,
            int32 ConditionY
        ) -> UEdGraphPin*
        {
            UEdGraphPin* Result = nullptr;
            for (int32 Index = 0; Index < KeyCount; ++Index)
            {
                UK2Node_CallFunction* Equal = AddCall(
                    Graph,
                    EqualByteFunction,
                    X + 260 + (Index % 8) * 200,
                    ConditionY + (Index / 8) * 105
                );
                Link(Schema, HCodePin, Pin(Equal, TEXT("A")));
                SetByteDefault(Schema, Pin(Equal, TEXT("B")), Keys[Index]);
                UEdGraphPin* EqualResult = Pin(Equal, TEXT("ReturnValue"));
                if (!Result)
                {
                    Result = EqualResult;
                    continue;
                }
                UK2Node_CallFunction* Or = AddCall(
                    Graph,
                    OrFunction,
                    X + 1960 + Index * 45,
                    ConditionY + Index * 34
                );
                Link(Schema, Result, Pin(Or, TEXT("A")));
                Link(Schema, EqualResult, Pin(Or, TEXT("B")));
                Result = Pin(Or, TEXT("ReturnValue"));
            }
            return Result;
        };

        const uint8 AlphaKeys[] = {
            17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
            33, 34, 35, 36, 37, 38, 39, 40, 41,
            46, 47, 48, 49, 50, 51, 52
        };
        const uint8 NavKeys[] = { 57, 65, 66, 67 };
        UEdGraphPin* Conditions[] = {
            BuildSetCondition(
                AlphaKeys,
                UE_ARRAY_COUNT(AlphaKeys),
                Y - 1200
            ),
            BuildSetCondition(
                NavKeys,
                UE_ARRAY_COUNT(NavKeys),
                Y + 200
            )
        };
        if (!Conditions[0] || !Conditions[1])
        {
            return false;
        }

        const float Retentions[] = { 0.982f, 0.960f };
        const float Gains[] = { 0.018f, 0.040f };
        UEdGraphPin* NewValues[2] = {};
        for (int32 Index = 0; Index < 2; ++Index)
        {
            const int32 ValueY = Y + Index * 500;
            UK2Node_VariableGet* OldValue = AddGet(
                Graph,
                ShareVariables[Index],
                X + 3500,
                ValueY
            );
            UK2Node_CallFunction* Retained = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(OldValue, *ShareVariables[Index].ToString()),
                Retentions[Index],
                X + 3740,
                ValueY
            );
            UK2Node_CallFunction* Sample = AddSelectFloat(
                Graph,
                Conditions[Index],
                1.0f,
                0.0f,
                X + 3500,
                ValueY + 150
            );
            UK2Node_CallFunction* WeightedSample = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(Sample, TEXT("ReturnValue")),
                Gains[Index],
                X + 3740,
                ValueY + 150
            );
            UK2Node_CallFunction* Added = AddCall(
                Graph,
                AddFunction,
                X + 3980,
                ValueY
            );
            Link(
                Schema,
                Pin(Retained, TEXT("ReturnValue")),
                Pin(Added, TEXT("A"))
            );
            Link(
                Schema,
                Pin(WeightedSample, TEXT("ReturnValue")),
                Pin(Added, TEXT("B"))
            );
            UK2Node_CallFunction* Clamped = AddCall(
                Graph,
                ClampFunction,
                X + 4220,
                ValueY
            );
            Link(
                Schema,
                Pin(Added, TEXT("ReturnValue")),
                Pin(Clamped, TEXT("Value"))
            );
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Min")), 0.0f);
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Max")), 1.0f);
            NewValues[Index] = Pin(Clamped, TEXT("ReturnValue"));
        }

        const TCHAR* MpcNames[] = {
            TEXT("MoodAlphaShare"),
            TEXT("MoodNavShare")
        };
        UEdGraphPin* ExecOut = Pin(PressedBranch, TEXT("then"));
        for (int32 Index = 0; Index < 2; ++Index)
        {
            UK2Node_VariableSet* SetValue = AddSet(
                Graph,
                ShareVariables[Index],
                X + 4540 + Index * 520,
                Y
            );
            Link(Schema, ExecOut, Pin(SetValue, TEXT("execute")));
            Link(
                Schema,
                NewValues[Index],
                Pin(SetValue, *ShareVariables[Index].ToString())
            );
            UK2Node_CallFunction* SetMpc = AddMpcSetter(
                Graph,
                Collection,
                MpcNames[Index],
                NewValues[Index],
                X + 4780 + Index * 520,
                Y
            );
            Link(
                Schema,
                Pin(SetValue, TEXT("then")),
                Pin(SetMpc, TEXT("execute"))
            );
            ExecOut = Pin(SetMpc, TEXT("then"));
        }

        return true;
    }

    bool AddBilateralShareBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    BilateralShareMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        const FName ShareVariables[] = {
            FName(TEXT("MoodfieldAlphaLeftShare")),
            FName(TEXT("MoodfieldAlphaRightShare"))
        };
        for (const FName Variable : ShareVariables)
        {
            EnsureVariable(
                Blueprint,
                Variable,
                UEdGraphSchema_K2::PC_Float,
                TEXT("0.0")
            );
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* BilateralExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                BilateralExec = Candidate;
                break;
            }
        }
        if (!BilateralExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 10300;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = BilateralShareMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, BilateralExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* EqualByteFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    EqualEqual_ByteByte
                )
            );
        UFunction* OrFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    BooleanOR
                )
            );
        UFunction* MultiplyFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Multiply_FloatFloat
                )
            );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UFunction* ClampFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    FClamp
                )
            );
        if (
            !EqualByteFunction
            || !OrFunction
            || !MultiplyFunction
            || !AddFunction
            || !ClampFunction
        )
        {
            return false;
        }

        auto BuildSetCondition = [&](
            const uint8* Keys,
            int32 KeyCount,
            int32 ConditionY
        ) -> UEdGraphPin*
        {
            UEdGraphPin* Result = nullptr;
            for (int32 Index = 0; Index < KeyCount; ++Index)
            {
                UK2Node_CallFunction* Equal = AddCall(
                    Graph,
                    EqualByteFunction,
                    X + 260 + (Index % 8) * 200,
                    ConditionY + (Index / 8) * 105
                );
                Link(Schema, HCodePin, Pin(Equal, TEXT("A")));
                SetByteDefault(Schema, Pin(Equal, TEXT("B")), Keys[Index]);
                UEdGraphPin* EqualResult = Pin(Equal, TEXT("ReturnValue"));
                if (!Result)
                {
                    Result = EqualResult;
                    continue;
                }

                UK2Node_CallFunction* Or = AddCall(
                    Graph,
                    OrFunction,
                    X + 1960 + Index * 45,
                    ConditionY + Index * 34
                );
                Link(Schema, Result, Pin(Or, TEXT("A")));
                Link(Schema, EqualResult, Pin(Or, TEXT("B")));
                Result = Pin(Or, TEXT("ReturnValue"));
            }
            return Result;
        };

        // Conventional QWERTY touch-typing groups.  The exact split is less
        // important than observing durable participation from both groups.
        const uint8 LeftAlphaKeys[] = {
            17, 18, 19, 20, 21,
            33, 34, 35, 36, 37,
            46, 47, 48, 49, 50
        };
        const uint8 RightAlphaKeys[] = {
            22, 23, 24, 25, 26,
            38, 39, 40, 41,
            51, 52
        };
        UEdGraphPin* Conditions[] = {
            BuildSetCondition(
                LeftAlphaKeys,
                UE_ARRAY_COUNT(LeftAlphaKeys),
                Y - 900
            ),
            BuildSetCondition(
                RightAlphaKeys,
                UE_ARRAY_COUNT(RightAlphaKeys),
                Y + 100
            )
        };
        if (!Conditions[0] || !Conditions[1])
        {
            return false;
        }

        UEdGraphPin* NewValues[2] = {};
        for (int32 Index = 0; Index < 2; ++Index)
        {
            const int32 ValueY = Y + Index * 500;
            UK2Node_VariableGet* OldValue = AddGet(
                Graph,
                ShareVariables[Index],
                X + 3200,
                ValueY
            );
            UK2Node_CallFunction* Retained = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(OldValue, *ShareVariables[Index].ToString()),
                0.976f,
                X + 3440,
                ValueY
            );
            UK2Node_CallFunction* Sample = AddSelectFloat(
                Graph,
                Conditions[Index],
                1.0f,
                0.0f,
                X + 3200,
                ValueY + 150
            );
            UK2Node_CallFunction* WeightedSample = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(Sample, TEXT("ReturnValue")),
                0.024f,
                X + 3440,
                ValueY + 150
            );
            UK2Node_CallFunction* Added = AddCall(
                Graph,
                AddFunction,
                X + 3680,
                ValueY
            );
            Link(
                Schema,
                Pin(Retained, TEXT("ReturnValue")),
                Pin(Added, TEXT("A"))
            );
            Link(
                Schema,
                Pin(WeightedSample, TEXT("ReturnValue")),
                Pin(Added, TEXT("B"))
            );
            UK2Node_CallFunction* Clamped = AddCall(
                Graph,
                ClampFunction,
                X + 3920,
                ValueY
            );
            Link(
                Schema,
                Pin(Added, TEXT("ReturnValue")),
                Pin(Clamped, TEXT("Value"))
            );
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Min")), 0.0f);
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Max")), 1.0f);
            NewValues[Index] = Pin(Clamped, TEXT("ReturnValue"));
        }

        const TCHAR* MpcNames[] = {
            TEXT("MoodAlphaLeftShare"),
            TEXT("MoodAlphaRightShare")
        };
        UEdGraphPin* ExecOut = Pin(PressedBranch, TEXT("then"));
        for (int32 Index = 0; Index < 2; ++Index)
        {
            UK2Node_VariableSet* SetValue = AddSet(
                Graph,
                ShareVariables[Index],
                X + 4240 + Index * 520,
                Y
            );
            Link(Schema, ExecOut, Pin(SetValue, TEXT("execute")));
            Link(
                Schema,
                NewValues[Index],
                Pin(SetValue, *ShareVariables[Index].ToString())
            );
            UK2Node_CallFunction* SetMpc = AddMpcSetter(
                Graph,
                Collection,
                MpcNames[Index],
                NewValues[Index],
                X + 4480 + Index * 520,
                Y
            );
            Link(
                Schema,
                Pin(SetValue, TEXT("then")),
                Pin(SetMpc, TEXT("execute"))
            );
            ExecOut = Pin(SetMpc, TEXT("then"));
        }

        return true;
    }

    bool AddProseZoneBridge(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (!Blueprint || !Collection || Blueprint->UbergraphPages.Num() == 0)
        {
            return false;
        }

        UEdGraph* Graph = Blueprint->UbergraphPages[0];
        const UEdGraphSchema_K2* Schema =
            GetDefault<UEdGraphSchema_K2>();
        for (UEdGraphNode* Existing : Graph->Nodes)
        {
            if (
                Existing
                && Existing->NodeComment.Equals(
                    ProseZoneMarker.ToString(),
                    ESearchCase::CaseSensitive
                )
            )
            {
                return true;
            }
        }

        const FName ZoneVariables[] = {
            FName(TEXT("MoodfieldProseTopLeft")),
            FName(TEXT("MoodfieldProseTopRight")),
            FName(TEXT("MoodfieldProseMiddleLeft")),
            FName(TEXT("MoodfieldProseMiddleRight")),
            FName(TEXT("MoodfieldProseBottomLeft")),
            FName(TEXT("MoodfieldProseBottomRight"))
        };
        for (const FName Variable : ZoneVariables)
        {
            EnsureVariable(
                Blueprint,
                Variable,
                UEdGraphSchema_K2::PC_Float,
                TEXT("0.0")
            );
        }

        UEdGraphNode* RawEvent = nullptr;
        UEdGraphPin* HCodePin = nullptr;
        UEdGraphPin* ActuatedPin = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            UEdGraphPin* HCode = Pin(Node, TEXT("HCode"));
            UEdGraphPin* Actuated = Pin(Node, TEXT("IsActuated"));
            UEdGraphPin* Then = Pin(Node, TEXT("then"));
            if (HCode && Actuated && Then)
            {
                RawEvent = Node;
                HCodePin = HCode;
                ActuatedPin = Actuated;
                break;
            }
        }
        if (!RawEvent || !HCodePin || !ActuatedPin)
        {
            return false;
        }

        UEdGraphPin* EventThen = Pin(RawEvent, TEXT("then"));
        UK2Node_ExecutionSequence* RootSequence = nullptr;
        if (EventThen && EventThen->LinkedTo.Num() > 0)
        {
            RootSequence = Cast<UK2Node_ExecutionSequence>(
                EventThen->LinkedTo[0]->GetOwningNode()
            );
        }
        if (!RootSequence)
        {
            return false;
        }

        RootSequence->Modify();
        RootSequence->AddInputPin();
        UEdGraphPin* ZoneExec = nullptr;
        for (int32 Index = RootSequence->Pins.Num() - 1; Index >= 0; --Index)
        {
            UEdGraphPin* Candidate = RootSequence->Pins[Index];
            if (
                Candidate
                && Candidate->Direction == EGPD_Output
                && Candidate->PinType.PinCategory
                    == UEdGraphSchema_K2::PC_Exec
                && Candidate->LinkedTo.Num() == 0
            )
            {
                ZoneExec = Candidate;
                break;
            }
        }
        if (!ZoneExec)
        {
            return false;
        }

        const int32 X = RawEvent->NodePosX + 520;
        const int32 Y = RawEvent->NodePosY + 12800;
        UK2Node_IfThenElse* PressedBranch =
            AddNode<UK2Node_IfThenElse>(Graph, X, Y);
        PressedBranch->NodeComment = ProseZoneMarker.ToString();
        PressedBranch->bCommentBubbleVisible = true;
        Link(Schema, ZoneExec, Pin(PressedBranch, TEXT("execute")));
        Link(Schema, ActuatedPin, Pin(PressedBranch, TEXT("Condition")));

        UFunction* EqualByteFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    EqualEqual_ByteByte
                )
            );
        UFunction* OrFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    BooleanOR
                )
            );
        UFunction* MultiplyFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Multiply_FloatFloat
                )
            );
        UFunction* AddFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    Add_FloatFloat
                )
            );
        UFunction* ClampFunction =
            UKismetMathLibrary::StaticClass()->FindFunctionByName(
                GET_FUNCTION_NAME_CHECKED(
                    UKismetMathLibrary,
                    FClamp
                )
            );
        if (
            !EqualByteFunction
            || !OrFunction
            || !MultiplyFunction
            || !AddFunction
            || !ClampFunction
        )
        {
            return false;
        }

        auto BuildSetCondition = [&](
            const uint8* Keys,
            int32 KeyCount,
            int32 ConditionY
        ) -> UEdGraphPin*
        {
            UEdGraphPin* Result = nullptr;
            for (int32 Index = 0; Index < KeyCount; ++Index)
            {
                UK2Node_CallFunction* Equal = AddCall(
                    Graph,
                    EqualByteFunction,
                    X + 260 + Index * 200,
                    ConditionY
                );
                Link(Schema, HCodePin, Pin(Equal, TEXT("A")));
                SetByteDefault(Schema, Pin(Equal, TEXT("B")), Keys[Index]);
                UEdGraphPin* EqualResult = Pin(Equal, TEXT("ReturnValue"));
                if (!Result)
                {
                    Result = EqualResult;
                    continue;
                }

                UK2Node_CallFunction* Or = AddCall(
                    Graph,
                    OrFunction,
                    X + 1360 + Index * 190,
                    ConditionY
                );
                Link(Schema, Result, Pin(Or, TEXT("A")));
                Link(Schema, EqualResult, Pin(Or, TEXT("B")));
                Result = Pin(Or, TEXT("ReturnValue"));
            }
            return Result;
        };

        const uint8 TopLeftKeys[] = { 17, 18, 19, 20, 21 };
        const uint8 TopRightKeys[] = { 22, 23, 24, 25, 26 };
        const uint8 MiddleLeftKeys[] = { 33, 34, 35, 36, 37 };
        const uint8 MiddleRightKeys[] = { 38, 39, 40, 41 };
        const uint8 BottomLeftKeys[] = { 46, 47, 48, 49, 50 };
        const uint8 BottomRightKeys[] = { 51, 52 };
        const uint8* KeySets[] = {
            TopLeftKeys,
            TopRightKeys,
            MiddleLeftKeys,
            MiddleRightKeys,
            BottomLeftKeys,
            BottomRightKeys
        };
        const int32 KeyCounts[] = {
            UE_ARRAY_COUNT(TopLeftKeys),
            UE_ARRAY_COUNT(TopRightKeys),
            UE_ARRAY_COUNT(MiddleLeftKeys),
            UE_ARRAY_COUNT(MiddleRightKeys),
            UE_ARRAY_COUNT(BottomLeftKeys),
            UE_ARRAY_COUNT(BottomRightKeys)
        };

        UEdGraphPin* Conditions[6] = {};
        for (int32 Index = 0; Index < 6; ++Index)
        {
            Conditions[Index] = BuildSetCondition(
                KeySets[Index],
                KeyCounts[Index],
                Y - 1800 + Index * 520
            );
            if (!Conditions[Index])
            {
                return false;
            }
        }

        UEdGraphPin* NewValues[6] = {};
        for (int32 Index = 0; Index < 6; ++Index)
        {
            const int32 ValueY = Y + Index * 430;
            UK2Node_VariableGet* OldValue = AddGet(
                Graph,
                ZoneVariables[Index],
                X + 3200,
                ValueY
            );
            UK2Node_CallFunction* Retained = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(OldValue, *ZoneVariables[Index].ToString()),
                0.980f,
                X + 3440,
                ValueY
            );
            UK2Node_CallFunction* Sample = AddSelectFloat(
                Graph,
                Conditions[Index],
                1.0f,
                0.0f,
                X + 3200,
                ValueY + 145
            );
            UK2Node_CallFunction* WeightedSample = AddFloatMath(
                Graph,
                MultiplyFunction,
                Pin(Sample, TEXT("ReturnValue")),
                0.020f,
                X + 3440,
                ValueY + 145
            );
            UK2Node_CallFunction* Added = AddCall(
                Graph,
                AddFunction,
                X + 3680,
                ValueY
            );
            Link(
                Schema,
                Pin(Retained, TEXT("ReturnValue")),
                Pin(Added, TEXT("A"))
            );
            Link(
                Schema,
                Pin(WeightedSample, TEXT("ReturnValue")),
                Pin(Added, TEXT("B"))
            );
            UK2Node_CallFunction* Clamped = AddCall(
                Graph,
                ClampFunction,
                X + 3920,
                ValueY
            );
            Link(
                Schema,
                Pin(Added, TEXT("ReturnValue")),
                Pin(Clamped, TEXT("Value"))
            );
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Min")), 0.0f);
            SetFloatDefault(Schema, Pin(Clamped, TEXT("Max")), 1.0f);
            NewValues[Index] = Pin(Clamped, TEXT("ReturnValue"));
        }

        const TCHAR* MpcNames[] = {
            TEXT("MoodProseTopLeft"),
            TEXT("MoodProseTopRight"),
            TEXT("MoodProseMiddleLeft"),
            TEXT("MoodProseMiddleRight"),
            TEXT("MoodProseBottomLeft"),
            TEXT("MoodProseBottomRight")
        };
        UEdGraphPin* ExecOut = Pin(PressedBranch, TEXT("then"));
        for (int32 Index = 0; Index < 6; ++Index)
        {
            UK2Node_VariableSet* SetValue = AddSet(
                Graph,
                ZoneVariables[Index],
                X + 4240 + Index * 500,
                Y
            );
            Link(Schema, ExecOut, Pin(SetValue, TEXT("execute")));
            Link(
                Schema,
                NewValues[Index],
                Pin(SetValue, *ZoneVariables[Index].ToString())
            );
            UK2Node_CallFunction* SetMpc = AddMpcSetter(
                Graph,
                Collection,
                MpcNames[Index],
                NewValues[Index],
                X + 4480 + Index * 500,
                Y
            );
            Link(
                Schema,
                Pin(SetValue, TEXT("then")),
                Pin(SetMpc, TEXT("execute"))
            );
            ExecOut = Pin(SetMpc, TEXT("then"));
        }

        return true;
    }

    bool RunClassifierSelfTest(
        UBlueprint* Blueprint,
        UMaterialParameterCollection* Collection
    )
    {
        if (
            !Blueprint
            || !Blueprint->GeneratedClass
            || !Collection
            || !GEditor
        )
        {
            return false;
        }

        UWorld* World = GEditor->GetEditorWorldContext().World();
        if (!World)
        {
            return false;
        }

        UFunction* KeyEvent = nullptr;
        for (
            TFieldIterator<UFunction> FunctionIt(
                Blueprint->GeneratedClass,
                EFieldIteratorFlags::ExcludeSuper
            );
            FunctionIt;
            ++FunctionIt
        )
        {
            UFunction* Candidate = *FunctionIt;
            if (
                FindFProperty<FByteProperty>(
                    Candidate,
                    FName(TEXT("HCode"))
                )
                && FindFProperty<FBoolProperty>(
                    Candidate,
                    FName(TEXT("IsActuated"))
                )
            )
            {
                KeyEvent = Candidate;
                break;
            }
        }
        if (!KeyEvent)
        {
            UE_LOG(
                LogTemp,
                Error,
                TEXT("Moodfield self-test could not find the key event.")
            );
            return false;
        }

        FActorSpawnParameters SpawnParameters;
        SpawnParameters.ObjectFlags |= RF_Transient;
        AActor* Actor = World->SpawnActor<AActor>(
            Blueprint->GeneratedClass,
            FTransform::Identity,
            SpawnParameters
        );
        if (!Actor)
        {
            return false;
        }

        TArray<uint8> Parameters;
        Parameters.SetNumZeroed(KeyEvent->ParmsSize);
        if (FByteProperty* HCode = FindFProperty<FByteProperty>(
            KeyEvent,
            FName(TEXT("HCode"))
        ))
        {
            HCode->SetPropertyValue_InContainer(
                Parameters.GetData(),
                static_cast<uint8>(33)
            );
        }
        if (FBoolProperty* IsActuated = FindFProperty<FBoolProperty>(
            KeyEvent,
            FName(TEXT("IsActuated"))
        ))
        {
            IsActuated->SetPropertyValue_InContainer(
                Parameters.GetData(),
                true
            );
        }
        if (FIntProperty* Percentage = FindFProperty<FIntProperty>(
            KeyEvent,
            FName(TEXT("Percentage"))
        ))
        {
            Percentage->SetPropertyValue_InContainer(
                Parameters.GetData(),
                100
            );
        }

        const float Before = UKismetMaterialLibrary::GetScalarParameterValue(
            Actor,
            Collection,
            FName(TEXT("MoodGlobal"))
        );
        const float BeforeLeft =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodLeft"))
            );
        const float BeforeMassLeft =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodMassLeft"))
            );
        Actor->ProcessEvent(KeyEvent, Parameters.GetData());
        const float AfterGlobal =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodGlobal"))
            );
        const float AfterTyping =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodTyping"))
            );
        const float AfterKey =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodKeyCode"))
            );
        const float AfterContact =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodContactCode"))
            );
        const float AfterEventClock =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodEventClock"))
            );
        const float AfterTrailCode =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodTrail0Code"))
            );
        const float AfterLeft =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodLeft"))
            );
        const float AfterMassLeft =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodMassLeft"))
            );
        const float AfterWasdShare =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodWasdShare"))
            );
        const float AfterAlphaShare =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodAlphaShare"))
            );
        const float AfterAlphaLeftShare =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodAlphaLeftShare"))
            );
        const float AfterProseMiddleLeft =
            UKismetMaterialLibrary::GetScalarParameterValue(
                Actor,
                Collection,
                FName(TEXT("MoodProseMiddleLeft"))
            );
        Actor->Destroy();

        UE_LOG(
            LogTemp,
            Display,
            TEXT(
                "Moodfield classifier self-test (%s): global %.3f -> %.3f, "
                "typing %.3f, key %.0f, contact %.0f, app clock %.3f, "
                "trail %.0f, left %.3f -> %.3f, mass %.3f -> %.3f, "
                "wasd %.3f, alpha %.3f, alpha-left %.3f, prose-ML %.3f."
            ),
            *KeyEvent->GetName(),
            Before,
            AfterGlobal,
            AfterTyping,
            AfterKey,
            AfterContact,
            AfterEventClock,
            AfterTrailCode,
            BeforeLeft,
            AfterLeft,
            BeforeMassLeft,
            AfterMassLeft,
            AfterWasdShare,
            AfterAlphaShare,
            AfterAlphaLeftShare,
            AfterProseMiddleLeft
        );
        return (
            AfterGlobal != Before
            && AfterKey == 33.0f
            && AfterContact == 33.0f
            && AfterEventClock > 0.0f
            && AfterTrailCode == 33.0f
            && AfterLeft > BeforeLeft
            && AfterMassLeft > BeforeMassLeft
            && AfterWasdShare > 0.0f
            && AfterAlphaShare > 0.0f
            && AfterAlphaLeftShare > 0.0f
            && AfterProseMiddleLeft > 0.0f
        );
    }
}
#endif

bool UMoodfieldAuthoringLibrary::ConfigureMoodfieldAssets()
{
    // UE4.27 commandlets can assert while retargeting a duplicated
    // Blueprint's widget-typed member.  Keep the public compatibility entry
    // point, but route it through the same path used by every device-tested
    // build: mutate a working copy of Keyfield Pulse in place.
    return ConfigureMoodfieldRuntimeAssets();

#if WITH_EDITOR
    static const TCHAR* WidgetPath =
        TEXT("/Game/CPPRO/Moodfield/WBP_Moodfield.WBP_Moodfield");
    static const TCHAR* BaseWidgetPath =
        TEXT(
            "/Game/CPPRO/KeyfieldPulse/"
            "WBP_KeyfieldPulse.WBP_KeyfieldPulse"
        );
    static const TCHAR* ActorPath =
        TEXT("/Game/CPPRO/Moodfield/BP_Moodfield.BP_Moodfield");
    static const TCHAR* MaterialPath =
        TEXT(
            "/Game/CPPRO/Moodfield/Materials/"
            "M_MoodfieldSurface.M_MoodfieldSurface"
        );
    static const TCHAR* CollectionPath =
        TEXT(
            "/Game/CPPRO/Moodfield/Materials/"
            "MPC_Moodfield.MPC_Moodfield"
        );

    UWidgetBlueprint* WidgetBlueprint =
        LoadObject<UWidgetBlueprint>(nullptr, WidgetPath);
    UWidgetBlueprint* BaseWidgetBlueprint =
        LoadObject<UWidgetBlueprint>(nullptr, BaseWidgetPath);
    UBlueprint* ActorBlueprint = LoadObject<UBlueprint>(nullptr, ActorPath);
    UMaterialInterface* SurfaceMaterial =
        LoadObject<UMaterialInterface>(nullptr, MaterialPath);
    UMaterialParameterCollection* Collection =
        LoadObject<UMaterialParameterCollection>(nullptr, CollectionPath);

    if (
        !WidgetBlueprint
        || !BaseWidgetBlueprint
        || !ActorBlueprint
        || !SurfaceMaterial
        || !Collection
    )
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield authoring assets could not be loaded.")
        );
        return false;
    }

    UBorder* Background = Cast<UBorder>(
        WidgetBlueprint->WidgetTree
            ? WidgetBlueprint->WidgetTree->FindWidget(
                FName(TEXT("MapBackground"))
            )
            : nullptr
    );
    if (!Background)
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield MapBackground border was not found.")
        );
        return false;
    }

    Background->Modify();
    Background->SetBrushFromMaterial(SurfaceMaterial);
    // UBorder keeps its existing BrushColor when its brush resource changes.
    // KeyfieldPulse intentionally used an almost-black tint here, which would
    // multiply a generated UI material down to an effectively black surface.
    // Generated full-field skins must start from a neutral host tint.
    Background->SetBrushColor(FLinearColor::White);
    if (!MoodfieldAuthoring::DisableLegacyForegroundEffects(
        WidgetBlueprint
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield foreground effects could not be disabled.")
        );
        return false;
    }
    WidgetBlueprint->Modify();
    // UE 4.27's generic asset duplication can retain the source widget's
    // generated class as ParentClass.  Reset it to the source Blueprint's real
    // parent (normally UUserWidget) before compiling the duplicate.
    WidgetBlueprint->ParentClass = BaseWidgetBlueprint->ParentClass;
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(
        WidgetBlueprint
    );
    FKismetEditorUtilities::CompileBlueprint(WidgetBlueprint);

    struct FVariableTypeChange
    {
        FName Name;
        FEdGraphPinType Type;
    };
    TArray<FVariableTypeChange> VariableTypeChanges;
    for (const FBPVariableDescription& Variable : ActorBlueprint->NewVariables)
    {
        UObject* SubCategoryObject = Variable.VarType
            .PinSubCategoryObject.Get();
        if (
            !SubCategoryObject
            || SubCategoryObject->GetName()
                != TEXT("WBP_KeyfieldPulse_C")
        )
        {
            continue;
        }

        FEdGraphPinType NewType = Variable.VarType;
        NewType.PinSubCategoryObject =
            WidgetBlueprint->GeneratedClass.Get();
        VariableTypeChanges.Add({Variable.VarName, NewType});
    }

    for (const FVariableTypeChange& Change : VariableTypeChanges)
    {
        FBlueprintEditorUtils::ChangeMemberVariableType(
            ActorBlueprint,
            Change.Name,
            Change.Type
        );
    }

    bool bUpdatedCreateWidget = false;
    for (UEdGraph* Graph : ActorBlueprint->UbergraphPages)
    {
        if (!Graph)
        {
            continue;
        }

        for (UEdGraphNode* Node : Graph->Nodes)
        {
            if (
                !Node
                || Node->GetClass()->GetName()
                    != TEXT("K2Node_CreateWidget")
            )
            {
                continue;
            }

            UEdGraphPin* ClassPin = Node->FindPin(FName(TEXT("Class")));
            if (!ClassPin || !WidgetBlueprint->GeneratedClass)
            {
                continue;
            }

            Node->Modify();
            ClassPin->Modify();
            ClassPin->DefaultObject = WidgetBlueprint->GeneratedClass;
            ClassPin->DefaultValue.Empty();
            bUpdatedCreateWidget = true;
        }
    }

    if (!bUpdatedCreateWidget)
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield Create Widget node was not found.")
        );
        return false;
    }

    ActorBlueprint->Modify();
    if (!MoodfieldAuthoring::AddClassifier(ActorBlueprint, Collection))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield adaptive classifier could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddEventClockBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield event clock bridge could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddTrailBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield trail bridge could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddMoodMemoryBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield regional memory could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddLongMoodBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield long-term mass could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddPatternShareBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield pattern shares could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddBilateralShareBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield bilateral alpha shares could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddProseZoneBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield prose zone memories could not be created.")
        );
        return false;
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(ActorBlueprint);
    FKismetEditorUtilities::CompileBlueprint(ActorBlueprint);
    if (!MoodfieldAuthoring::RunClassifierSelfTest(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime classifier self-test failed.")
        );
        return false;
    }

    WidgetBlueprint->MarkPackageDirty();
    ActorBlueprint->MarkPackageDirty();
    UE_LOG(
        LogTemp,
        Display,
        TEXT("Moodfield widget material and actor widget class configured.")
    );
    return true;
#else
    return false;
#endif
}

bool UMoodfieldAuthoringLibrary::ConfigureMoodfieldRuntimeAssets()
{
#if WITH_EDITOR
    UWidgetBlueprint* WidgetBlueprint = LoadObject<UWidgetBlueprint>(
        nullptr,
        TEXT(
            "/Game/CPPRO/KeyfieldPulse/"
            "WBP_KeyfieldPulse.WBP_KeyfieldPulse"
        )
    );
    UBlueprint* ActorBlueprint = LoadObject<UBlueprint>(
        nullptr,
        TEXT(
            "/Game/CPPRO/KeyfieldPulse/"
            "BP_KeyfieldPulse.BP_KeyfieldPulse"
        )
    );
    UMaterialInterface* SurfaceMaterial =
        LoadObject<UMaterialInterface>(
            nullptr,
            TEXT(
                "/Game/CPPRO/Moodfield/Materials/"
                "M_MoodfieldSurface.M_MoodfieldSurface"
            )
        );
    UMaterialParameterCollection* Collection =
        LoadObject<UMaterialParameterCollection>(
            nullptr,
            TEXT(
                "/Game/CPPRO/Moodfield/Materials/"
                "MPC_Moodfield.MPC_Moodfield"
            )
        );

    if (
        !WidgetBlueprint
        || !ActorBlueprint
        || !SurfaceMaterial
        || !Collection
    )
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime authoring assets could not be loaded.")
        );
        return false;
    }

    UBorder* Background = Cast<UBorder>(
        WidgetBlueprint->WidgetTree
            ? WidgetBlueprint->WidgetTree->FindWidget(
                FName(TEXT("MapBackground"))
            )
            : nullptr
    );
    if (!Background)
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime MapBackground was not found.")
        );
        return false;
    }

    Background->Modify();
    Background->SetBrushFromMaterial(SurfaceMaterial);
    // Do not inherit KeyfieldPulse's near-black background tint.  UMG
    // multiplies the UI material by this value at draw time.
    Background->SetBrushColor(FLinearColor::White);
    if (!MoodfieldAuthoring::DisableLegacyForegroundEffects(
        WidgetBlueprint
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT(
                "Moodfield runtime foreground effects could not be disabled."
            )
        );
        return false;
    }
    WidgetBlueprint->Modify();
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(
        WidgetBlueprint
    );
    FKismetEditorUtilities::CompileBlueprint(WidgetBlueprint);

    ActorBlueprint->Modify();
    if (!MoodfieldAuthoring::AddClassifier(ActorBlueprint, Collection))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime classifier could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddEventClockBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime event clock bridge could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddTrailBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime trail bridge could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddMoodMemoryBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime regional memory could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddLongMoodBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime long-term mass could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddPatternShareBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime pattern shares could not be created.")
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddBilateralShareBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT(
                "Moodfield runtime bilateral alpha shares "
                "could not be created."
            )
        );
        return false;
    }
    if (!MoodfieldAuthoring::AddProseZoneBridge(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime prose zones could not be created.")
        );
        return false;
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(ActorBlueprint);
    FKismetEditorUtilities::CompileBlueprint(ActorBlueprint);
    if (!MoodfieldAuthoring::RunClassifierSelfTest(
        ActorBlueprint,
        Collection
    ))
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("Moodfield runtime classifier self-test failed.")
        );
        return false;
    }

    WidgetBlueprint->MarkPackageDirty();
    ActorBlueprint->MarkPackageDirty();
    UE_LOG(
        LogTemp,
        Display,
        TEXT("Moodfield runtime assets configured in place.")
    );
    return true;
#else
    return false;
#endif
}
