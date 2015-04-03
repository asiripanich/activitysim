import os
import urbansim.sim.simulation as sim
from activitysim import activitysim as asim
import pandas as pd
import numpy as np

"""
The workplace location model predicts the zones in which various people will
work.  Interestingly there's not really any supply side to this model - we
assume that in a properly calibrated model there are workplaces for the people
to work.
"""


@sim.injectable()
def workplace_location_spec(configs_dir):
    f = os.path.join(configs_dir, 'configs', "workplace_location.csv")
    return asim.read_model_spec(f).fillna(0)


# FIXME there's enough here that this needs to be a utility in activitysim
# FIXME core and documented and tested
@sim.table()
def workplace_size_terms(land_use, destination_choice_size_terms):
    """
    This method takes the land use data and multiplies various columns of the
    land use data by coefficients from the workplace_size_spec table in order
    to yield a size term (a linear combination of land use variables) with
    specified coefficients for different segments (like low, med, and high
    income)
    """
    land_use = land_use.to_frame()

    df = destination_choice_size_terms.to_frame().query("purpose == 'work'")
    df = df.drop("purpose", axis=1).set_index("segment")

    new_df = {}
    for index, row in df.iterrows():

        missing = row[~row.index.isin(land_use.columns)]

        if len(missing) > 0:
            print "WARNING: missing columns in land use\n", missing.index

        row = row[row.index.isin(land_use.columns)]
        sparse = land_use[list(row.index)]
        new_df["size_"+index] = np.dot(sparse.as_matrix(), row.values)

    new_df = pd.DataFrame(new_df, index=land_use.index)
    return new_df


# FIXME there are three school models that go along with this one which have
# FIXME not been implemented yet
@sim.model()
def workplace_location_simulate(set_random_seed,
                                persons_merged,
                                zones,
                                workplace_location_spec,
                                skims,
                                workplace_size_terms):

    choosers = persons_merged.to_frame()
    alternatives = zones.to_frame().join(workplace_size_terms.to_frame())

    # set the keys for this lookup - in this case there is a TAZ in the choosers
    # and a TAZ in the alternatives which get merged during interaction
    skims.set_keys("TAZ", "TAZ_r")
    # the skims will be available under the name "skims" for any @ expressions
    locals_d = {"skims": skims}

    choices, _ = asim.interaction_simulate(
        choosers, alternatives, workplace_location_spec, skims=skims,
        locals_d=locals_d, sample_size=50)

    print "Describe of choices:\n", choices.describe()
    sim.add_column("persons", "workplace_taz", choices)