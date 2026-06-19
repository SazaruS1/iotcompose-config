function decodeUplink(input) {
    var bytes = input.bytes;
    var offset = 0;

    // Vérifier la longueur: 4 bytes = alerte batterie
    if (bytes.length === 4) {
        
        
        function readInt16LE(scale) {
            var val = bytes[offset] | (bytes[offset + 1] << 8);
            if (val > 32767) val -= 65536;
            offset += 2;
            return (val / scale).toFixed(scale === 1 ? 0 : 2);
        }
        
        var battery = parseFloat(readInt16LE(100));
        var alertCode = (bytes[2] | (bytes[3] << 8)).toString(16).toUpperCase();
        
        return {
            data: {
                alert_type: "BATTERY_LOW",
                battery_voltage: battery + " V",
                alert_code: "0x" + alertCode,
                message: "ALERTE BATTERIE Faible"
            },
            warnings: [],
            errors: []
        };
    }
    
    function readInt16LE(scale) {
        var val = bytes[offset] | (bytes[offset + 1] << 8);
        if (val > 32767) val -= 65536;
        offset += 2;
        return (val / scale).toFixed(scale === 1 ? 0 : 2);
    }

    return {
        data: {
            // ===== API du CR1000 Datalogger (9 valeurs) =====
            BattV_Avg: parseFloat(readInt16LE(100)),
            AirT_C_Avg: parseFloat(readInt16LE(10)),
            RH: parseFloat(readInt16LE(10)),
            SlrHoriz_W_Avg: parseFloat(readInt16LE(1)),
            SlrHoriz_MJ_Tot: parseFloat(readInt16LE(100)),
            SlrTilt_W_Avg: parseFloat(readInt16LE(1)),
            SlrTilt_MJ_Tot: parseFloat(readInt16LE(100)),
            WS_ms_S_WVT: parseFloat(readInt16LE(100)),
            WindDir_D1_WVT: parseFloat(readInt16LE(1)),

            // ===== Capteur MS5637 =====
            MS5637_Pressure: parseFloat(readInt16LE(10)),
            
            // ===== Capteur UV =====
            UV_Voltage: parseFloat(readInt16LE(1)),
            UV_Index: parseFloat(readInt16LE(1)),

            // ===== Capteur Pyranomètre =====
            Pyrano_Radiation: parseFloat(readInt16LE(1)),

            // ===== Pluviomètre =====
            Rain_mm_Tot: parseFloat(readInt16LE(10))
        },
        warnings: [],
        errors: []
    };
}

function encodeDownlink(input) {
    return {
        bytes: [0x01],
        fport: 8
    };
}