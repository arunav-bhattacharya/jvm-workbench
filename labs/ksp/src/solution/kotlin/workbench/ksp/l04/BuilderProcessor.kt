package workbench.ksp.l04

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSValueParameter
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.CodeBlock
import com.squareup.kotlinpoet.FileSpec
import com.squareup.kotlinpoet.FunSpec
import com.squareup.kotlinpoet.KModifier
import com.squareup.kotlinpoet.PropertySpec
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.ksp.addOriginatingKSFile
import com.squareup.kotlinpoet.ksp.toClassName
import com.squareup.kotlinpoet.ksp.toTypeName
import com.squareup.kotlinpoet.ksp.writeTo
import workbench.ksp.annotations.Builder

// Lesson 4, reference answer: the @Builder processor, written with KotlinPoet.

/** KSP creates the processor through this provider. Registered in workbench/ksp/l04/SymbolProcessorProvider. */
class BuilderProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        BuilderProcessor(environment.codeGenerator, environment.logger)
}

/**
 * For each class annotated [Builder], generates `<Name>Builder` in `<Name>Builder.kt`: one private field and one
 * setter per primary constructor parameter, and `build()`.
 */
class BuilderProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    // KSP 2.3.14's warning-free style: say which newer API behaviours this processor accepts
    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    // Given code: while the lab is unfinished this logs a warning and generates nothing,
    // so a real build with -Pmine still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        processBuilders(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l04 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    /**
     * Given code, the five moves:
     * 1. Find the classes annotated @Builder.
     * 2. Check: skip what isn't a class declaration (lesson 5 makes this move much stricter).
     * 3. Read the primary constructor's parameters, and 4. Write one file per class with KotlinPoet:
     *    [builderFile] builds the file, and writeTo hands it to KSP with the class's file as its origin.
     * 5. Prove: the tests, then `./gradlew :ksp:app:kspL04Kotlin`.
     */
    fun processBuilders(resolver: Resolver): List<KSAnnotated> {
        val symbols = resolver.getSymbolsWithAnnotation(Builder::class.qualifiedName!!).toList()
        for (symbol in symbols) {
            if (symbol !is KSClassDeclaration) {
                logger.error("@Builder goes on a class", symbol)
                continue
            }
            // aggregating = false: this builder depends only on its own class's file (the originating file)
            builderFile(symbol).writeTo(codeGenerator, aggregating = false)
        }
        return emptyList()
    }
}

/** The builder's name: `LampBuilder` for `Lamp`, `KitchenDrawerBuilder` for the nested `Kitchen.Drawer`. */
fun builderName(cls: KSClassDeclaration): ClassName {
    val target = cls.toClassName()
    return ClassName(target.packageName, target.simpleNames.joinToString("") + "Builder")
}

/** The primary constructor's parameters. Lesson 5 turns this `!!` into a real check. */
fun constructorParameters(cls: KSClassDeclaration): List<KSValueParameter> = cls.primaryConstructor!!.parameters

/** A parameter's name as written, for example `name` (or `in` for a parameter written `` `in` ``). */
fun nameOf(param: KSValueParameter): String = param.name!!.asString()

/**
 * 4. Write, the field: `private var name: String? = null`, a `var` (`mutable(true)`) that starts as `null`.
 * Its type is the parameter's type (`param.type.toTypeName()`) made nullable with `copy(nullable = true)`,
 * because every field starts empty; `shade: String?` stays `String?`, and `List<Box?>?` stays `List<Box?>?`.
 */
fun builderProperty(param: KSValueParameter): PropertySpec =
    PropertySpec.builder(nameOf(param), param.type.toTypeName().copy(nullable = true), KModifier.PRIVATE)
        .mutable(true)
        .initializer("null")
        .build()

/**
 * 4. Write, a setter that returns the builder, so calls chain. Its one parameter has the parameter's own type.
 * Write names with `%N`, so a name such as `in` comes out as `` `in` ``:
 * ```
 * public fun name(name: String): LampBuilder {
 *   this.name = name
 *   return this
 * }
 * ```
 */
fun setterFunction(param: KSValueParameter, builder: ClassName): FunSpec {
    val name = nameOf(param)
    return FunSpec.builder(name)
        .addParameter(name, param.type.toTypeName())
        .returns(builder)
        .addStatement("this.%N = %N", name, name)
        .addStatement("return this")
        .build()
}

/**
 * Given code, `build()`: calls the class's constructor with named arguments. A parameter whose type is nullable
 * may stay unset (it passes null); every other one must be set, or build() stops with a clear message.
 * KSP sees that a parameter has a default value, never what the value is, so a default doesn't make it optional.
 * ```
 * public fun build(): Lamp = Lamp(
 *   name = name ?: error("LampBuilder: name was not set"),
 *   bulbs = bulbs ?: error("LampBuilder: bulbs was not set"),
 *   shade = shade,
 * )
 * ```
 */
fun buildFunction(cls: KSClassDeclaration, builder: ClassName): FunSpec {
    val call = CodeBlock.builder().add("return %T(\n", cls.toClassName()).indent()
    for (param in constructorParameters(cls)) {
        val name = nameOf(param)
        if (param.type.toTypeName().isNullable) {
            call.add("%N = %N,\n", name, name)
        } else {
            call.add("%N = %N ?: error(%S),\n", name, name, "${builder.simpleName}: $name was not set")
        }
    }
    call.unindent().add(")\n")
    return FunSpec.builder("build").returns(cls.toClassName()).addCode(call.build()).build()
}

/**
 * 4. Write, the class: `public class LampBuilder` with one [builderProperty] and one [setterFunction] per
 * constructor parameter (in order), then [buildFunction]. Its originating file is the class's own file.
 */
fun builderType(cls: KSClassDeclaration): TypeSpec {
    val builder = builderName(cls)
    val params = constructorParameters(cls)
    return TypeSpec.classBuilder(builder)
        .addProperties(params.map(::builderProperty))
        .addFunctions(params.map { setterFunction(it, builder) })
        .addFunction(buildFunction(cls, builder))
        .addOriginatingKSFile(cls.containingFile!!)
        .build()
}

/**
 * 4. Write, the file: `<package>/LampBuilder.kt`, holding [builderType], with this first line (for a nested class,
 * `from Kitchen.Drawer`: join `cls.toClassName().simpleNames` with dots):
 * `// Generated by BuilderProcessor from Lamp. Do not edit.`
 */
fun builderFile(cls: KSClassDeclaration): FileSpec {
    val builder = builderName(cls)
    return FileSpec.builder(builder)
        .addFileComment("Generated by BuilderProcessor from %L. Do not edit.", cls.toClassName().simpleNames.joinToString("."))
        .addType(builderType(cls))
        .build()
}
