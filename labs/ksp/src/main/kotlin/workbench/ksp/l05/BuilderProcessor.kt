package workbench.ksp.l05

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.isPrivate
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSValueParameter
import com.google.devtools.ksp.validate
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

// Lesson 5, the lab: lesson 4's @Builder processor, copied into this package as given code (`describe` and
// everything after it). Your job is the two functions marked TODO: processBuilders (the five moves, now with validate()
// and without stopping at the first problem) and check (report each problem on the exact symbol).

/** KSP creates the processor through this provider. Registered in workbench/ksp/l05/SymbolProcessorProvider. */
class BuilderProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        BuilderProcessor(environment.codeGenerator, environment.logger)
}

/** For each class annotated [Builder] that passes [check], generates `<Name>Builder`, as in lesson 4. */
class BuilderProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    // Given code: while the lab is unfinished this logs a warning and generates nothing,
    // so a real build with -Pmine still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        processBuilders(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l05 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    /**
     * The five moves, with lesson 5's changes:
     * 1. Find the symbols annotated @Builder. Split them with `validate(apiFeatures = apiFeatures)`: a symbol whose
     *    types can't be resolved yet is returned from process(), so KSP offers it again next round (lesson 6).
     * 2. Check each valid symbol with [check]. A failed check skips that symbol only: carry on with the others,
     *    so one build reports every problem.
     * 3. Read and 4. Write each symbol that passed: `builderFile(cls).writeTo(codeGenerator, aggregating = false)`.
     * 5. Prove: the tests, then `./gradlew :ksp:app:kspL05Kotlin`.
     */
    fun processBuilders(resolver: Resolver): List<KSAnnotated> {
        TODO("processBuilders: find the @Builder symbols, set aside the invalid ones, check and write the rest")
    }

    /**
     * 2. Check, before you read. Reports each problem on the exact symbol and returns true only if a builder can
     * be written. The messages say what is wrong and how to fix it; the symbol says where.
     * - Not a class (an interface, an object, an enum class...): an error on the class,
     *   `@Builder needs a class to build, but Wardrobe is an interface. Put @Builder on a class with a primary constructor.`
     * - No primary constructor: an error on the class,
     *   `Crate has no primary constructor, so CrateBuilder doesn't know what to pass. Declare the properties in one: class Crate(val label: String).`
     * - A private primary constructor: an error on the constructor,
     *   `SafeBuilder can't call Safe's constructor, because it is private. Make it internal or public, or remove @Builder.`
     * - A parameter with a default value is not a reason to stop: a warning on the parameter,
     *   `PlantBuilder can't see the default value of waterEveryDays, so build() will require it. Set it on the builder.`
     */
    fun check(symbol: KSAnnotated): Boolean {
        TODO("check: report a symbol that isn't a class, has no primary constructor or a private one; warn about defaults")
    }
}

/** Given: "Wardrobe is an interface", "Settings is an object", "Size is an enum class". */
fun describe(symbol: KSAnnotated): String {
    if (symbol !is KSClassDeclaration) return "$symbol is not a class"
    val kind = symbol.classKind.name.lowercase().replace('_', ' ')
    return "${symbol.simpleName.asString()} is ${if (kind.first() in "aeiou") "an" else "a"} $kind"
}

/** The builder's name: `LampBuilder` for `Lamp`, `KitchenDrawerBuilder` for the nested `Kitchen.Drawer`. */
fun builderName(cls: KSClassDeclaration): ClassName {
    val target = cls.toClassName()
    return ClassName(target.packageName, target.simpleNames.joinToString("") + "Builder")
}

/** The primary constructor's parameters. [BuilderProcessor.check] makes sure there is a primary constructor. */
fun constructorParameters(cls: KSClassDeclaration): List<KSValueParameter> = cls.primaryConstructor!!.parameters

/** A parameter's name as written, for example `name` (or `in` for a parameter written `` `in` ``). */
fun nameOf(param: KSValueParameter): String = param.name!!.asString()

/**
 * Given (lesson 4), the field: `private var name: String? = null`. The type is the parameter's own type made nullable,
 * because every field starts empty; `shade: String?` stays `String?`, and `List<Box?>?` stays `List<Box?>?`.
 */
fun builderProperty(param: KSValueParameter): PropertySpec =
    PropertySpec.builder(nameOf(param), param.type.toTypeName().copy(nullable = true), KModifier.PRIVATE)
        .mutable(true)
        .initializer("null")
        .build()

/**
 * Given (lesson 4), a setter that returns the builder, so calls chain:
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
 * Given (lesson 4), `build()`: calls the class's constructor with named arguments. A parameter whose type is nullable
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
 * Given (lesson 4), the class: `public class LampBuilder` with one [builderProperty] and one [setterFunction] per
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

/** Given (lesson 4), the file: `<package>/LampBuilder.kt`, with a comment that names its class, and [builderType]. */
fun builderFile(cls: KSClassDeclaration): FileSpec {
    val builder = builderName(cls)
    return FileSpec.builder(builder)
        .addFileComment("Generated by BuilderProcessor from %L. Do not edit.", cls.toClassName().simpleNames.joinToString("."))
        .addType(builderType(cls))
        .build()
}
