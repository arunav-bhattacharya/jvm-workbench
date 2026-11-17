package workbench.kotlin.l02

/** "Parcel 1.250 kg". The JVM name is parcelLabel-<hash>(long): Kotlin callers only. */
fun parcelLabel(weight: Weight): String = "Parcel $weight kg"

/**
 * The same label for Java callers. @JvmName removes the hash, so Java can call
 * LabelsKt.parcelLabelForJava(1250L). Java passes a raw long that never went through Weight's init,
 * so validate again: Weight(weight.grams) runs the init block.
 */
@JvmName("parcelLabelForJava")
fun parcelLabelJava(weight: Weight): String = parcelLabel(Weight(weight.grams))

/** Returns Weight, so Java receives a plain long. Top-level functions are mangled only for value-class parameters. */
fun parseWeight(kilograms: String): Weight = Weight.parse(kilograms)
