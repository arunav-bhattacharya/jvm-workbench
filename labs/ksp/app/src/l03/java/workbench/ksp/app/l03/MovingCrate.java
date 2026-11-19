package workbench.ksp.app.l03;

import workbench.ksp.annotations.Label;

// A box labeled in another language: KSP reads Java sources in the same source set too (origin JAVA).
// Java has no primary constructor, and nothing says whether a Java String may be null, so the label prints
// MovingCrate(label: String!, weightGrams: Int).
@Label
public class MovingCrate {
    private final String label;
    private final int weightGrams;

    public MovingCrate(String label, int weightGrams) {
        this.label = label;
        this.weightGrams = weightGrams;
    }

    public String getLabel() {
        return label;
    }

    public int getWeightGrams() {
        return weightGrams;
    }
}
