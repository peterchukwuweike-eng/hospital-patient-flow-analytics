from pyspark.sql.functions import * 

# we need this configuration to connect to the event hubs
event_hub_namespace = "<<Namespace_hostname>>"
event_hub_name="<<Eventhub_Name>>"  
event_hub_conn_str = dbutils.secrets.get(scope="", key="")


kafka_options = {
    'kafka.bootstrap.servers': f"{event_hub_namespace}:9093",
    'subscribe': event_hub_name,
    'kafka.security.protocol': 'SASL_SSL',
    'kafka.sasl.mechanism': 'PLAIN',
    'kafka.sasl.jaas.config': f'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required username="$ConnectionString" password="{event_hub_conn_str}";',
    'startingOffsets': 'latest',
    'failOnDataLoss': 'false'
}

#Read from eventhub
raw_df = (spark.readStream
          .format("kafka")
          .options(**kafka_options)
          .load()
            )

#cast the data to json strings
json_df = raw_df.selectExpr("CAST(value AS STRING) as raw_json")

#connection to azure datalake 
spark.conf.set(
  "fs.azure.account.key.<<Storageaccount_name>>.dfs.core.windows.net",
  dbutils.secrets.get(scope="", key="")
)
#path to write the data
bronze_path = "abfss://bronze@<<Storageaccount_name>>.dfs.core.windows.net/patient_flow"



#Write stream to bronze
(
    json_df
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "abfss://bronze@<<Storageaccount_name>>.dfs.core.windows.net/_checkpoints/patient_flow")
    .start(bronze_path)
)


