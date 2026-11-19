package workbench.ksp.annotations

/**
 * Lesson 3: marks a property whose contents break easily. The processor reads it on constructor
 * properties.
 */
@Target(AnnotationTarget.PROPERTY, AnnotationTarget.VALUE_PARAMETER)
@Retention(AnnotationRetention.SOURCE)
annotation class Fragile
