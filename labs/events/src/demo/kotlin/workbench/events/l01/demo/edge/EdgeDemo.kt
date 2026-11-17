package workbench.events.l01.demo.edge

@JvmInline
value class ParcelId(val value: String) {
    init { require(Regex("PP-[0-9]{4,12}").matches(value)) { "invalid parcel id: '$value'" } }
    override fun toString(): String = value
}

@JvmInline
value class Weight(val grams: Long) {
    init { require(grams >= 0) { "weight must not be negative: $grams" } }
    override fun toString(): String = "$grams g"
}

sealed interface ParcelEvent { val parcelId: ParcelId }
data class ParcelCollected(override val parcelId: ParcelId, val weight: Weight) : ParcelEvent
data class ParcelDelivered(override val parcelId: ParcelId, val weight: Weight) : ParcelEvent

sealed interface Parsed {
    data class Ok(val event: ParcelEvent) : Parsed
    data class Rejected(val reason: String) : Parsed
}

/** The edge: raw fields in, a model value or a reason out. It never throws. */
fun parse(fields: Map<String, String>): Parsed {
    fun field(name: String) = fields[name] ?: throw IllegalArgumentException("missing field '$name'")
    fun weight(): Weight {
        val raw = field("grams")
        return Weight(raw.toLongOrNull() ?: throw IllegalArgumentException("grams is not a whole number: '$raw'"))
    }
    return try {
        when (val type = field("type")) {
            "collected" -> Parsed.Ok(ParcelCollected(ParcelId(field("parcelId")), weight()))
            "delivered" -> Parsed.Ok(ParcelDelivered(ParcelId(field("parcelId")), weight()))
            else -> Parsed.Rejected("unknown event type: '$type'")
        }
    } catch (e: IllegalArgumentException) {
        Parsed.Rejected(e.message ?: "invalid event")       // a constructor or a reader said no
    }
}

fun main() {
    val inbox = listOf(
        mapOf("type" to "collected", "parcelId" to "PP-7781", "grams" to "2500"),
        mapOf("type" to "collected", "parcelId" to "PP-7782", "grams" to "2.5"),
        mapOf("type" to "delivered", "parcelId" to "7781", "grams" to "2500"),
        mapOf("type" to "delivered", "parcelId" to "PP-7781", "grams" to "-500"),
        mapOf("type" to "collected", "parcelId" to "PP-7783"),
        mapOf("type" to "failed", "parcelId" to "PP-7784", "reason" to "NOBODY_HOME"),
    )
    var accepted = 0
    for (fields in inbox) {
        when (val p = parse(fields)) {
            is Parsed.Ok -> { accepted++; println("OK        ${p.event}") }
            is Parsed.Rejected -> println("REJECTED  ${p.reason}")
        }
    }
    println("$accepted accepted, ${inbox.size - accepted} rejected")
}
