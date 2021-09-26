# Rasperry PI Temperature modelling using Azure Synapse Analytics

## End to End example to collect Temperature and build model

## Architecture

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/rasppianalytics.jpg "Logo Title Text 1")

## Azure Resource

- Create Azure IoT Hub
- Create Storage Account
- Create Stream Analytics
- Create Azure Synapse Analytics

## Raspberry PI 

- The above architecture show end to end
- Use Raspberry PI 4 Model B
- Load Noobs with Raspian OS
- Install IoT Edge
- Create a IoT Edge device in Azure IoT Hub and note the connection string
- Apply the connection string to rasperry pi's IoT configuration
- Download and install sample temperature docker module as iot edge module

## Cloud programming

- Go to Stream Analytics
- Create a input as iot hub

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspiot4.jpg "Logo Title Text 1")

- Create a output 

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspiot5.jpg "Logo Title Text 1")

- Create a query

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspiot1.jpg "Logo Title Text 1")

- Input data 

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspiot2.jpg "Logo Title Text 1")

- Output sample

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspiot3.jpg "Logo Title Text 1")

- Now start the Stream ANalytics
- Check the storage and you should see the data saved as parquet

![alt text](https://github.com/balakreshnan/raspiot/blob/main/images/raspiot6.jpg "Logo Title Text 1")

## Now to Modelling

- Go to Azure Synapse Analytics
- Go to Develop
- Create a new pyspark notebook
- i am using spark 3 as spark engine
- Start your code

- import library

```
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.feature import IndexToString, StringIndexer, VectorIndexer
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.sql import functions as f
from pyspark.ml.feature import VectorAssembler
```

- read the data

```
%%pyspark
df = spark.read.load('abfss://containername@sccountname.dfs.core.windows.net/raspinput/*/*/*/*.parquet', format='parquet')
display(df.limit(10))
```

```
from pyspark.sql.functions import *
```

- Create new columns

```
df = df.withColumn("year", year(df.timeCreated))
df = df.withColumn("month", month(df.timeCreated))
df = df.withColumn("day", dayofmonth(df.timeCreated))
df = df.withColumn("hour", hour(df.timeCreated))
df = df.withColumn("minute", minute(df.timeCreated))
```

- Choose columns needed

```
traindf = df[["MachTemp", "pressure", "AmbTemp","humidity","year", "month", "day", "hour", "minute"]]
```

- create categorical columns

```
categoricalColumns = [item[0] for item in traindf.dtypes if item[1].startswith('string') ]
```

- Set features column

```
featurescol = ["MachTemp", "pressure", "AmbTemp","humidity","year", "month", "day", "hour", "minute"]
```

- now setup the spark pipeline

```
stages = []
#iterate through all categorical values
for categoricalCol in categoricalColumns:
    #create a string indexer for those categorical values and assign a new name including the word 'Index'
    stringIndexer = StringIndexer(inputCol = categoricalCol, outputCol = categoricalCol + 'Index')

    #append the string Indexer to our list of stages
    stages += [stringIndexer]
```

- format the features and labels

```
labelIndexer = StringIndexer(inputCol="MachTemp", outputCol="indexedLabel").fit(traindf)

#assembler = VectorAssembler(inputCols=featurescol, outputCol="features")
assembler = VectorAssembler(inputCols=featurescol, outputCol="features")

#featureIndexer = VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(titanicds1)


(trainingData, testData) = traindf.randomSplit([0.7, 0.3])
```

- transform

```
assembler = VectorAssembler(
    inputCols=["MachTemp", "pressure", "AmbTemp","humidity","year", "month", "day", "hour", "minute"],
    outputCol="features")

output = assembler.transform(traindf)
```

- output label

```
output = output.withColumn("labels", output.MachTemp)
```

- Train the model

```
from pyspark.ml.regression import LinearRegression

lr = LinearRegression(maxIter=10, regParam=0.3, elasticNetParam=0.8).setLabelCol("MachTemp")

# Fit the model
lrModel = lr.fit(output)
```

- validate the model performance

```
# Print the coefficients and intercept for linear regression
print("Coefficients: %s" % str(lrModel.coefficients))
print("Intercept: %s" % str(lrModel.intercept))

# Summarize the model over the training set and print out some metrics
trainingSummary = lrModel.summary
print("numIterations: %d" % trainingSummary.totalIterations)
print("objectiveHistory: %s" % str(trainingSummary.objectiveHistory))
trainingSummary.residuals.show()
print("RMSE: %f" % trainingSummary.rootMeanSquaredError)
print("r2: %f" % trainingSummary.r2)
```

```
output = output.withColumn("label", output.MachTemp)
```

- next another algorithmn model

```
from pyspark.ml import Pipeline
from pyspark.ml.regression import DecisionTreeRegressor
from pyspark.ml.feature import VectorIndexer
from pyspark.ml.evaluation import RegressionEvaluator

# Load the data stored in LIBSVM format as a DataFrame.
#data = spark.read.format("libsvm").load("data/mllib/sample_libsvm_data.txt")

# Automatically identify categorical features, and index them.
# We specify maxCategories so features with > 4 distinct values are treated as continuous.
featureIndexer =\
    VectorIndexer(inputCol="features", outputCol="indexedFeatures", maxCategories=4).fit(output)

# Split the data into training and test sets (30% held out for testing)
(trainingData, testData) = output.randomSplit([0.7, 0.3])

# Train a DecisionTree model.
dt = DecisionTreeRegressor(featuresCol="indexedFeatures")

# Chain indexer and tree in a Pipeline
pipeline = Pipeline(stages=[featureIndexer, dt])

# Train model.  This also runs the indexer.
model = pipeline.fit(trainingData)

# Make predictions.
predictions = model.transform(testData)

# Select example rows to display.
predictions.select("prediction", "label", "features").show(5)

# Select (prediction, true label) and compute test error
evaluator = RegressionEvaluator(
    labelCol="label", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)
print("Root Mean Squared Error (RMSE) on test data = %g" % rmse)

treeModel = model.stages[1]
# summary only
print(treeModel)
```