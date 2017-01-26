// german translations for the app specific part

var MSG = {
    buttonRun: "Los",
    buttonStop: "Stopp!",
    buttonConnect: "Verbinde",
    stateDisconnected: "getrennt",
    stateConnected: "verbunden",
    stateConnecting: "verbinde...",
    stateRunning: "läuft...",
    stateProgramEnded: "beendet",

    // messages
    confirm_delete: "Wirklich das ganze Programm '%1' löschen?",
    delete_not_connected: "Zum Löschen des ganzen Programms muss der TXT verbunden sein",

    // the menu
    dropdown_new: "Neu",
    dropdown_del: "Löschen",

    // the skill system
    skillToolTip: "Wähle Erfahrungsgrad '%1' aus.",
    skill1: "Anfänger",
    skill2: "Junior",
    skill3: "Fortgeschritten",
    skill4: "Senior",
    skill5: "Experte",
    
    // blocks
    blockStartToolTip: "Hier startet die Programmausführung.",

    blockWaitMessage: "warte %1 Sekunden",
    blockWaitToolTip: "Programm eine vorgegebene Zeit anhalten.",
    blockRepeatMessage: "wiederhole %1 %2",
    blockRepeatToolTip: "Wiederhole etwas endlos.",
    blockPwmValueMessage: "%1",
    blockPwmValueToolTip: "Variabler Ausgangszustand.",
    blockOnOffMessage: "%1",
    blockOnOffToolTip: "An/aus Ausgangszustand",

    blockMobileDriveMessage: "fahre %1 %2 cm",
    blockForward: "vorwärts",
    blockBackward: "rückwärts",
    blockMobileDriveToolTip: "Fahre eine bestimmte Strecke geradeaus",
    blockMobileTurnMessage: "drehe %1 %2",
    blockMobileTurnToolTip: "Auf der Stelle drehen",
    blockMobileConfigMessage: "Mobilroboter-Konfiguration %1 Motoren %2 und %3 vom Typ: %4 Antriebsübersetzung %5 : %6 %7 Raddurchmesser: %8 cm %9 Radabstand: %10 cm",
    blockMobileConfigToolTip: "Benutzerdefinierte Mobilroboter-Konfiguration. Wird nicht für das Discovery Set benötigt",
    blockMobileDriveWhileMessage: "fahre %1 %2 %3",
    blockMobileDriveWhileToolTip: "Fahre geradeaus bis ein Ereignis eintritt",
    blockWhile: "solange",
    blockUntil: "bis",

    blockOn: "ein",
    blockOff: "aus",

    blockAngleMessage: "%1",
    blockAngleToolTip: "Drehwinkel",
    blockRot45: "etwas herum",
    blockRot90: "halb herum",
    blockRot135: "weit herum",
    blockRot180: "ganz herum",

    blockIOSyncMessage: "gleichzeitig %1 %2",
    blockIOSyncToolTip: "Steuere Ausgänge gleichzeitig",

    blockInputModeVoltage: "Spannung (mV)",
    blockInputModeSwitch: "Schalterzustand",
    blockInputModeResistor: "Widerstand",
    blockInputModeResistor2: "Widerstand 2",
    blockInputModeUltrasonic: "Distanz (cm)",
    blockInputModeAnalog: "Analogwert",
    blockInputModeDigital: "Digitalwert",
    
    blockInputMessage: "%1 an Eingang %2",
    blockInputToolTip: "Lies den Wert eines Eingangs",

    blockInputConvTempMessage: "Temperatur %1 %2",
    blockInputConvTempToolTip: "Konvertiere Widerstandswert in Temperatur",

    blockSimpleInputMessage: "Eingang %1 ist an",
    blockSimpleInputToolTip: "Lies den Zustand eines Eingangs",
    
    blockOutputModeOutput: "Einzelausgänge",
    blockOutputModeMotor: "Motorausgang",

    blockOutputMessage: "schalte Ausgang %1 %2",
    blockOutputToolTip: "Schalte einen Einzelausgang",

    blockMotorMessage: "starte Motor %1 %2 mit %3",
    blockMotorToolTip: "Starte einen Motor",
    blockLeft: "links",
    blockRight: "rechts",

    blockMotorStepsMessage: "starte Motor %1 %2 mit %3 für %4 Umdrehungen",
    blockMotorStepsToolTip: "Starte einen Motor für eine vorgegebene Anzahl Umdrehungen",

    blockMotorSetMessage: "setze Motor %1 %2 auf %3",
    blockMotorSetToolTip: "Einen Motorwert setzen",
    blockMotorSetSpeed: 'Geschwindigkeit',
    blockMotorSetDir: 'Richtung',
    blockMotorSetDist: 'Entfernung',
    blockMotorSetGear: 'Typ',
    blockLeftRightMessage: "%1",
    blockLeftRightToolTip: "Drehrichtung links/rechts",
    blockGearMessage: "%1",
    blockGearToolTip: "Encoderimpulse pro Umdrehung",
    blockGearTXT: "neuer Encodermotor (TXT)",
    blockGearTX: "alter Encodermotor (TX)",
    blockMotorSyncMessage: "kopple Motoren %1 und %2",
    blockMotorSyncToolTip: "Zwei Motoren für Synchronlauf koppeln",

    blockMotorHasStoppedMessage: "Motor %1 hat gestoppt",
    blockMotorHasStoppedToolTip: "Teste, ob Motor gestoppt hat",

    blockMotorOffMessage: "stoppe Motor %1",
    blockMotorOffToolTip: "Schalte einen Motor aus",

    blockPlaySndMessage: "spiele Geräusch %1",
    blockPlaySndToolTip: "Spiele ein Geräusch ab",
    blockSoundMessage: "%1",
    blockSoundToolTip: "Geräuschauswahl",
    blockSoundAirplane: "Flugzeug",
    blockSoundAlarm: "Alarm",
    blockSoundBell: "Glocke",
    blockSoundBraking: "Bremsen",
    blockSoundCar_horn_long: "Hupe lang",
    blockSoundCar_horn_short: "Hupe kurz",
    blockSoundCrackling_wood: "Knisterndes Holz",
    blockSoundExcavator: "Bagger",
    blockSoundFantasy_1: "Fantasie 1",
    blockSoundFantasy_2: "Fantasie 2",
    blockSoundFantasy_3: "Fantasie 3",
    blockSoundFantasy_4: "Fantasie 4",
    blockSoundFarm: "Bauernhof",
    blockSoundFire_department: "Feuerwehr",
    blockSoundFire_noises: "Feuer",
    blockSoundFormula1: "Formel 1",
    blockSoundHelicopter: "Hubschrauber",
    blockSoundHydraulic: "Hydraulik",
    blockSoundMotor_sound: "Motorengeräusch",
    blockSoundMotor_starting: "Startender Motor",
    blockSoundPropeller_airplane: "Propellerflugzeug",
    blockSoundRoller_coaster: "Achterbahn",
    blockSoundShips_horn: "Schiffshorn",
    blockSoundTractor: "Traktor",
    blockSoundTruck: "Lastwagen",
    blockSoundRobby_1: "Robbie 1",
    blockSoundRobby_2: "Robbie 2",
    blockSoundRobby_3: "Robbie 3",
    blockSoundRobby_4: "Robbie 4",

    blockTextPrintColorMessage: "gib aus in %1 %2",
    blockTextPrintColorToolTip: "Gib einen Text in der angegebenen Farbe aus.",
    blockTextEraseMessage: "Text löschen",
    blockTextEraseToolTip: "Entferne allen Text vom Bildschirm.",

    textVariable: "Text",
    listVariable: "Liste",

    // categories
    catCustom: "Spezial",
    catInputs: "Eingänge",
    catOutputs: "Ausgänge",
    catMotors: "Motoren",
    catMobile: "Mobil",
    catLogic: "Logik",
    catLoops: "Schleifen",
    catMath: "Mathe",
    catText: "Text",
    catLists: "Listen",
    catVariables: "Variablen",
    catFunctions: "Funktionen"
}
