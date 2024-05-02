import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from typing import Any, Dict, List, Union

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_table = dynamodb.Table('inventory_info')

status_check_path: str = '/status'
inventory_path: str = '/inventory'
inventories_path: str = '/inventories'

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler for processing HTTP requests.

    Args:
        event (Dict[str, Any]): The event data from AWS Lambda.
        context (Any): The context object from AWS Lambda.

    Returns:
        Dict[str, Any]: The HTTP response.
    """
    print('Request event: ', event)
    response = None

    try:
        http_method: str = event.get('httpMethod')
        path: str = event.get('path')

        if http_method == 'GET' and path == status_check_path:
            response = build_response(200, 'Service is operational')
        elif http_method == 'GET' and path == inventory_path:
            inventory_id: str = event['queryStringParameters']['inventoryId']
            response = get_inventory(inventory_id)
        elif http_method == 'GET' and path == inventories_path:
            response = get_inventories()
        elif http_method == 'POST' and path == inventory_path:
            response = save_inventory(json.loads(event['body']))
        elif http_method == 'PATCH' and path == inventory_path:
            body: Dict[str, Any] = json.loads(event['body'])
            response = modify_inventory(body['inventoryId'], body['updateKey'], body['updateValue'])
        elif http_method == 'DELETE' and path == inventory_path:
            body: Dict[str, Any] = json.loads(event['body'])
            response = delete_inventory(body['inventoryId'])
        else:
            response = build_response(404, '404 Not Found')

    except Exception as e:
        print('Error:', e)
        response = build_response(400, 'Error processing request')

    return response

def get_inventory(inventory_id: str) -> Dict[str, Any]:
    """
    Retrieves inventory information from DynamoDB.

    Args:
        inventory_id (str): The ID of the inventory item.

    Returns:
        Dict[str, Any]: The HTTP response containing the inventory item.
    """
    try:
        response = dynamodb_table.get_item(Key={'inventoryId': inventory_id})
        return build_response(200, response.get('Item'))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def get_inventories() -> Dict[str, Any]:
    """
    Retrieves all inventories from DynamoDB.

    Returns:
        Dict[str, Any]: The HTTP response containing the list of inventories.
    """
    try:
        scan_params: Dict[str, str] = {'TableName': dynamodb_table.name}
        return build_response(200, scan_dynamo_records(scan_params, []))
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def scan_dynamo_records(scan_params: Dict[str, str], item_array: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Scans DynamoDB records recursively.

    Args:
        scan_params (Dict[str, str]): Parameters for scanning DynamoDB records.
        item_array (List[Dict[str, Any]]): List to store scanned items.

    Returns:
        Dict[str, Any]: The HTTP response containing the scanned items.
    """
    response = dynamodb_table.scan(**scan_params)
    item_array.extend(response.get('Items', []))

    if 'LastEvaluatedKey' in response:
        scan_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
        return scan_dynamo_records(scan_params, item_array)
    else:
        return {'inventories': item_array}

def save_inventory(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves inventory information to DynamoDB.

    Args:
        request_body (Dict[str, Any]): The request body containing inventory information.

    Returns:
        Dict[str, Any]: The HTTP response indicating the success of the operation.
    """
    try:
        dynamodb_table.put_item(Item=request_body)
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': request_body
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def modify_inventory(inventory_id: str, update_key: str, update_value: Any) -> Dict[str, Any]:
    """
    Modifies inventory information in DynamoDB.

    Args:
        inventory_id (str): The ID of the inventory item.
        update_key (str): The key to be updated.
        update_value (Any): The new value for the key.

    Returns:
        Dict[str, Any]: The HTTP response indicating the success of the operation.
    """
    try:
        response = dynamodb_table.update_item(
            Key={'inventoryId': inventory_id},
            UpdateExpression=f'SET {update_key} = :value',
            ExpressionAttributeValues={':value': update_value},
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'UpdatedAttributes': response
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

def delete_inventory(inventory_id: str) -> Dict[str, Any]:
    """
    Deletes inventory information from DynamoDB.

    Args:
        inventory_id (str): The ID of the inventory item to be deleted.

    Returns:
        Dict[str, Any]: The HTTP response indicating the success of the operation.
    """
    try:
        response = dynamodb_table.delete_item(
            Key={'inventoryId': inventory_id},
            ReturnValues='ALL_OLD'
        )
        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'Item': response
        }
        return build_response(200, body)
    except ClientError as e:
        print('Error:', e)
        return build_response(400, e.response['Error']['Message'])

class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for encoding Decimal objects.
    """
    def default(self, obj: Any) -> Union[int, float]:
        """
        Overrides the default JSON encoder method.

        Args:
            obj (Any): The object to encode.

        Returns:
            Union[int, float]: The encoded object.
        """
        if isinstance(obj, Decimal):
            # Check if it's an int or a float
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        # Let the base class default method raise the TypeError
        return super(DecimalEncoder, self).default(obj)

def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """
    Builds an HTTP response.

    Args:
        status_code (int): The HTTP status code.
        body (Any): The response body.

    Returns:
        Dict[str, Any]: The HTTP response.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
