package workbench.ksp.annotations

/**
 * Lessons 4 and 5: generate `<Class>Builder` with one setter per primary constructor property and `build()`.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Builder
