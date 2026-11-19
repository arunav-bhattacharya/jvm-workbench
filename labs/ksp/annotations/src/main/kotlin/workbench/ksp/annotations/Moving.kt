package workbench.ksp.annotations

/**
 * Lesson 6: generate a `<Class>Receipt` data class for this class. The receipt itself carries
 * `@Inventory`, so another processor gives it an inventory card in the next round.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Moving
