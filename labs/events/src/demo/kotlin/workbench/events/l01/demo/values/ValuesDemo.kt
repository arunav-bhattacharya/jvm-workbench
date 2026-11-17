package workbench.events.l01.demo.values

import java.math.BigDecimal

@JvmInline
value class ParcelId(val value: String) {
    init { require(Regex("PP-[0-9]{4,12}").matches(value)) { "invalid parcel id: '$value'" } }
    override fun toString(): String = value
}

@JvmInline
value class Weight(val grams: Long) {
    init { require(grams >= 0) { "weight must not be negative: $grams" } }
    override fun toString(): String = BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + " kg"
}

data class ParcelCollected(val parcelId: ParcelId, val weight: Weight)

/** A parcel described with raw types: nothing stops a caller from swapping the two Longs. */
data class RawParcel(val parcelId: String, val grams: Long, val centimetres: Long)

fun main() {
    println(ParcelCollected(ParcelId("PP-7781"), Weight(2_500)))
    println(RawParcel("PP-7781", 40, 2_500))              // swapped: a 40-gram parcel, 25 metres long

    // Step 2: uncomment. The arguments are in the wrong order.
    // println(ParcelCollected(Weight(2_500), ParcelId("PP-7781")))

    for (attempt in listOf({ ParcelId("7781") }, { Weight(-500) })) {
        try {
            attempt()
        } catch (e: IllegalArgumentException) {
            println("refused: ${e.message}")
        }
    }

    // What the JVM stores: the value classes are gone, only their one field is left
    for (f in ParcelCollected::class.java.declaredFields) println("field ${f.name}: ${f.type.name}")
}
