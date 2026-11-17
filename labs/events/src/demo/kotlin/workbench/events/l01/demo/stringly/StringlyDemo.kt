package workbench.events.l01.demo.stringly

// Three handlers each read the raw fields of a scan. Nothing checked the scan first.

var onTheBikeGrams = 0L
var textsSent = 0

fun tracking(fields: Map<String, String>) {
    println("tracking ${fields["type"]} ${fields["parcelId"]}")
}

fun loadBoard(fields: Map<String, String>) {
    val grams = when (fields["type"]) {
        "collected" -> fields.getValue("grams").toLong()          // parsing, deep inside a handler
        "delivered" -> -fields.getValue("grams").toLong()
        else -> return
    }
    onTheBikeGrams += grams
    println("load     %+d g, on the bike: %d g".format(grams, onTheBikeGrams))
}

fun texts(fields: Map<String, String>) {
    if (fields["type"] == "deliver") {                            // a typo the compiler can't see
        textsSent++
    }
}

fun main() {
    val scans = listOf(
        mapOf("type" to "collected", "parcelId" to "PP-7781", "grams" to "2500"),
        mapOf("type" to "delivered", "parcelId" to "PP-7781", "grams" to "2500"),
        mapOf("type" to "collected", "parcelId" to "PP-7782", "grams" to "2.5"),
    )
    for (scan in scans) {
        try {
            tracking(scan)
            loadBoard(scan)
            texts(scan)
        } catch (e: RuntimeException) {
            println("FAILED   $e")
        }
    }
    println("texts sent: $textsSent")
}
