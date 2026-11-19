package workbench.ksp.annotations.smoke

/**
 * Smoke example (keep or delete): put it on a class and the smoke processor generates
 * `fun helloFrom<ClassName>(): String` next to it.
 *
 * SOURCE retention is enough: KSP reads annotations from source code, and nothing needs them at run time.
 */
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Hello
