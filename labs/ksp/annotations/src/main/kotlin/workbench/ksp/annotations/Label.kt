package workbench.ksp.annotations

/**
 * Lesson 3: print this class's typed shape, for example `Lamp(name: String, bulbs: Int, shade: String?)`.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Label
