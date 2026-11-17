package workbench.startup.l03;

/**
 * A message from a depot: a parcel's barcode was scanned there. {@link EventDecoder} creates
 * and reads it only through reflection, the way a JSON library does. Don't change this class.
 */
public final class ParcelScanned {
    private final String parcelId;
    private final String depot;
    private final long weightGrams;

    public ParcelScanned(String parcelId, String depot, long weightGrams) {
        this.parcelId = parcelId;
        this.depot = depot;
        this.weightGrams = weightGrams;
    }

    public String parcelId() {
        return parcelId;
    }

    public String depot() {
        return depot;
    }

    public long weightGrams() {
        return weightGrams;
    }

    /** Nobody calls this reflectively, so it needs no metadata. */
    public String summary() {
        return parcelId + " scanned at " + depot + ", " + weightGrams + " g";
    }
}
