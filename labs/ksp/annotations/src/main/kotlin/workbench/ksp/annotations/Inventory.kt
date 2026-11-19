package workbench.ksp.annotations

/**
 * MoveMate's sticky note "make an inventory card for this one" (ksp track, lessons 1, 2, 6 and 7).
 * The lesson 2 processor generates `fun <Class>.inventoryCard(): String` for each class that carries it,
 * for example `Lamp: name=desk lamp, bulbs=1, shade=null`.
 *
 * KSP reads annotations from source code, so SOURCE retention would be enough for it. This one is kept
 * at RUNTIME so lesson 1 and lesson 9 can compare the generated card with a reflection version that looks
 * for the annotation while the program runs.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
annotation class Inventory
