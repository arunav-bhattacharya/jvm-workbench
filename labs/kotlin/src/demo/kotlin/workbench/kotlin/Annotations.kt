package workbench.kotlin

/*
 * Marker annotations for the compiler plugins configured in labs/kotlin/build.gradle.kts (lesson kt-06):
 *   allOpen { annotation("workbench.kotlin.OpenForProxies") }
 *   noArg { annotation("workbench.kotlin.NoArgEntity") }
 * They do nothing by themselves. The plugins look for their fully qualified names at compile time.
 */

/** all-open: the class and its members become open, so a framework can generate a subclass proxy. */
@Target(AnnotationTarget.CLASS)
annotation class OpenForProxies

/** no-arg: the compiler adds a zero-argument constructor, callable from Java and reflection only. */
@Target(AnnotationTarget.CLASS)
annotation class NoArgEntity
