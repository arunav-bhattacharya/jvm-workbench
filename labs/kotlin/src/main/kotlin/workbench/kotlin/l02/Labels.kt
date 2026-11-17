package workbench.kotlin.l02

/** "Parcel 1.250 kg". Kotlin callers only: its JVM name is parcelLabel-<hash>(long), which javac can't call. */
fun parcelLabel(weight: Weight): String = TODO("\"Parcel \$weight kg\"")

/*
 * TODO 7: an older Java program prints the same labels. Add a function here that Java can call as
 * LabelsKt.parcelLabelForJava(1250L) and that returns "Parcel 1.250 kg".
 *  - Its parameter is still a Weight. Give it the JVM name parcelLabelForJava with one annotation.
 *  - Java hands over a raw long that never went through Weight's init. Make -500L throw
 *    IllegalArgumentException anyway.
 */

/** Returns Weight, so Java receives a plain long. Finished: it works once Weight.parse does. */
fun parseWeight(kilograms: String): Weight = Weight.parse(kilograms)
