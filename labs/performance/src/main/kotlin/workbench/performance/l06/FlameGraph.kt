package workbench.performance.l06

/** One line of collapsed stacks: frames from the root (first) to the top (last), and a sample count. */
data class Sample(val frames: List<String>, val count: Long)

/**
 * The collapsed-stack format that async-profiler (`-o collapsed`) and flamegraph.pl use:
 *
 * ```
 * Thread.run;Worker.run;SlowFees.feeSlow;java/util/regex/Pattern.compile 645
 * ```
 * Frames are separated by `;`, and the count follows the last space. Frame names can contain spaces.
 */
object FlameGraph {

    /** Parses one line. Returns null for blank lines. */
    fun parse(line: String): Sample? {
        TODO("split on the LAST space: frames before it, count after it")
    }

    /** Samples per top frame (the last frame of each stack): where the CPU actually was. */
    fun selfTime(samples: List<Sample>): Map<String, Long> {
        TODO("add each sample's count to its last frame")
    }

    /**
     * Samples per frame, counting a frame once per sample even if it appears several times
     * in the same stack (recursion, or two methods with the same name).
     */
    fun inclusiveTime(samples: List<Sample>): Map<String, Long> {
        TODO("add each sample's count to every distinct frame in it")
    }

    /** Builds the flame graph tree under a root named "all". Equal prefixes merge into one box. */
    fun build(samples: List<Sample>): FlameNode {
        TODO("walk each stack from the root, adding the count to every node on the way")
    }

    /** From the root, keep stepping into the widest child until a leaf. Returns the names, without "all". */
    fun hottestPath(root: FlameNode): List<String> {
        TODO("follow maxBy { it.total } until there are no children")
    }
}
